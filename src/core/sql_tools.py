"""
SQL Tools implementation for the MCP server.
Handles SQL generation, validation, and execution.
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
import openai
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

class SQLTools:
    """Core SQL tools for the MCP server."""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    async def generate_sql(self, nl_query: str, db_type: str = "postgresql", schema_uri: str = None) -> str:
        """Generate SQL query from natural language description, and provide an explanation."""
        try:
            # Build system prompt with schema context if available
            system_prompt = f"""You are a SQL expert. Generate a valid {db_type} SQL query based on the natural language description.

Key guidelines:
- Use proper {db_type} syntax
- Include appropriate JOINs when needed
- Use meaningful table and column aliases
- Add comments explaining complex logic
- Ensure the query is safe and follows best practices
- Use the exact table and column names from the database schema

Return only the SQL query, no explanations."""

            # Add schema context if available
            if schema_uri:
                # Fetch schema data from resource manager
                from core.resource_manager import ResourceManager
                resource_manager = ResourceManager()
                
                try:
                    print(f"🔍 Attempting to load schema from: {schema_uri}")
                    # Read the schema resource
                    schema_content = await resource_manager.read_resource(schema_uri, raw=True)
                    print(f"📄 Schema content length: {len(schema_content) if schema_content else 0}")
                    
                    if schema_content and len(schema_content) > 0:
                        schema_text = schema_content[0].text
                        print(f"📝 Schema text preview: {schema_text[:200]}...")
                        
                        # Parse as JSON (should work now since we're getting raw data)
                        try:
                            schema_data = json.loads(schema_text)
                            print(f"✅ Schema parsed successfully with {len(schema_data.get('tables', {}))} tables")
                        except json.JSONDecodeError:
                            # Fallback to text parsing if needed
                            print(f"📋 Parsing formatted schema text...")
                            schema_data = self._extract_schema_from_text(schema_text)
                            print(f"📋 Extracted schema info: {len(schema_data.get('tables', {}))} tables")
                        
                        # Build schema context for the prompt
                        schema_context = f"\n\nDatabase Schema Information:\n"
                        schema_context += f"Database Type: {schema_data.get('database_type', 'unknown')}\n"
                        schema_context += f"Tables and their columns:\n"
                        
                        for table_name, table_info in schema_data.get('tables', {}).items():
                            schema_context += f"\nTable: {table_name}\n"
                            for col in table_info.get('columns', []):
                                pk_marker = " (PRIMARY KEY)" if col.get('primary_key') else ""
                                schema_context += f"  - {col['name']}: {col['type']}{pk_marker}\n"
                        
                        # Add relationships
                        relationships = schema_data.get('relationships', [])
                        if relationships:
                            schema_context += f"\nTable Relationships:\n"
                            for rel in relationships:
                                schema_context += f"  - {rel['table']}.{rel['column']} -> {rel['references']}\n"
                        
                        system_prompt += schema_context
                        system_prompt += f"\n\nIMPORTANT: Use ONLY the exact table and column names listed above. Do not use generic names like 'user_id', 'username', 'total_amount'."
                        print(f"📋 Schema context added to prompt")
                        
                except Exception as e:
                    print(f"❌ Warning: Could not load schema from {schema_uri}: {e}")
                    system_prompt += f"\n\nSchema reference: {schema_uri} (could not load)"

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": nl_query}
                ],
                temperature=0.3
            )
            sql_query = response.choices[0].message.content.strip()

            # Generate explanation for the SQL query
            explanation_prompt = "Explain the following SQL query in simple terms for a business user."
            explanation_response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": explanation_prompt},
                    {"role": "user", "content": f"SQL Query: {sql_query}\nPlease explain what this query does."}
                ],
                temperature=0.3
            )
            explanation = explanation_response.choices[0].message.content.strip()

            # Return structured result
            result = {
                "sql_query": sql_query,
                "explanation": explanation,
                "db_type": db_type,
                "nl_query": nl_query,
                "schema_uri": schema_uri,
                "status": "generated"
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "status": "failed"
            }, indent=2)
    
    async def validate_sql(self, sql_query: str) -> str:
        """Validate SQL query for syntax and safety."""
        try:
            # Basic SQL injection check
            dangerous_keywords = [
                "DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE", "INSERT", "UPDATE"
            ]
            
            sql_upper = sql_query.upper()
            has_dangerous_operations = any(keyword in sql_upper for keyword in dangerous_keywords)
            
            # Use OpenAI to analyze the query
            system_prompt = """Analyze this SQL query for:
1. Syntax correctness
2. Potential security issues
3. Performance considerations
4. Best practices

Return a JSON response with:
- valid: boolean
- issues: array of strings
- suggestions: array of strings
- risk_level: "low", "medium", "high"
"""

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": sql_query}
                ],
                temperature=0.1
            )
            
            analysis = response.choices[0].message.content.strip()
            
            # Try to parse as JSON, fallback to text if needed
            try:
                analysis_dict = json.loads(analysis)
            except:
                analysis_dict = {
                    "valid": True,
                    "issues": [],
                    "suggestions": [],
                    "risk_level": "low",
                    "raw_analysis": analysis
                }
            
            # Add our own checks
            if has_dangerous_operations:
                analysis_dict["risk_level"] = "high"
                analysis_dict["issues"].append("Contains potentially dangerous operations")
            
            result = {
                "sql_query": sql_query,
                "validation": analysis_dict,
                "status": "validated"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "status": "failed"
            }, indent=2)
    
    async def execute_sql(self, sql_query: str, db_connection: str = "sqlite:///./data/analytics.db") -> str:
        """Execute SQL query and return results as a table resource."""
        try:
            # Create engine
            engine = create_engine(db_connection)
            
            # Execute query
            with engine.connect() as conn:
                result = conn.execute(text(sql_query))
                
                # Fetch results
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    
                    # Convert to pandas DataFrame for easier handling
                    df = pd.DataFrame(rows, columns=columns)
                    
                    # Create table resource data
                    table_data = {
                        "sql_query": sql_query,
                        "columns": list(columns),
                        "row_count": len(rows),
                        "data": df.to_dict('records'),
                        "status": "executed"
                    }
                    
                    return json.dumps(table_data, indent=2, default=str)
                else:
                    # For non-SELECT queries
                    return json.dumps({
                        "sql_query": sql_query,
                        "message": "Query executed successfully (no results returned)",
                        "status": "executed"
                    }, indent=2)
                    
        except SQLAlchemyError as e:
            return json.dumps({
                "error": f"Database error: {str(e)}",
                "sql_query": sql_query,
                "status": "failed"
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "sql_query": sql_query,
                "status": "failed"
            }, indent=2)
    
    async def get_table_schema(self, table_name: str, db_connection: str = "sqlite:///./data/analytics.db") -> str:
        """Get schema information for a specific table."""
        try:
            engine = create_engine(db_connection)
            inspector = inspect(engine)
            
            # Get column information
            columns = inspector.get_columns(table_name)
            
            # Get primary keys
            pk = inspector.get_pk_constraint(table_name)
            
            # Get foreign keys
            fks = inspector.get_foreign_keys(table_name)
            
            schema_info = {
                "table_name": table_name,
                "columns": columns,
                "primary_keys": pk.get('constrained_columns', []),
                "foreign_keys": fks,
                "status": "retrieved"
            }
            
            return json.dumps(schema_info, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "table_name": table_name,
                "status": "failed"
            }, indent=2)
    
    async def discover_schema(self, connection_string: str, include_sample_data: bool = True, max_sample_rows: int = 5) -> str:
        """Discover database schema and store as MCP resource."""
        try:
            # Create engine
            engine = create_engine(connection_string)
            inspector = inspect(engine)
            
            # Get database type from connection string
            db_type = connection_string.split('://')[0] if '://' in connection_string else 'unknown'
            
            # Get all table names
            table_names = inspector.get_table_names()
            
            schema_data = {
                "database_type": db_type,
                "connection_string": connection_string,
                "tables": {},
                "relationships": [],
                "discovered_at": str(pd.Timestamp.now())
            }
            
            # Process each table
            for table_name in table_names:
                # Get column information
                columns = inspector.get_columns(table_name)
                column_info = []
                
                for col in columns:
                    column_info.append({
                        "name": col['name'],
                        "type": str(col['type']),
                        "nullable": col.get('nullable', True),
                        "primary_key": col.get('primary_key', False),
                        "default": col.get('default'),
                        "unique": col.get('unique', False)
                    })
                
                # Get primary keys
                pk = inspector.get_pk_constraint(table_name)
                primary_keys = pk.get('constrained_columns', [])
                
                # Get foreign keys
                fks = inspector.get_foreign_keys(table_name)
                foreign_keys = []
                for fk in fks:
                    foreign_keys.append({
                        "column": fk['constrained_columns'][0],
                        "references_table": fk['referred_table'],
                        "references_column": fk['referred_columns'][0]
                    })
                    # Add to global relationships
                    schema_data["relationships"].append({
                        "table": table_name,
                        "column": fk['constrained_columns'][0],
                        "references": f"{fk['referred_table']}.{fk['referred_columns'][0]}"
                    })
                
                # Get sample data if requested
                sample_data = []
                if include_sample_data:
                    try:
                        with engine.connect() as conn:
                            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {max_sample_rows}"))
                            rows = result.fetchall()
                            columns = result.keys()
                            
                            for row in rows:
                                sample_data.append(dict(zip(columns, row)))
                    except Exception as e:
                        sample_data = [{"error": f"Could not fetch sample data: {str(e)}"}]
                
                # Store table information
                schema_data["tables"][table_name] = {
                    "columns": column_info,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_keys,
                    "sample_data": sample_data,
                    "row_count": len(sample_data) if sample_data else 0
                }
            
            # Create schema resource
            schema_uri = f"resource://schemas/{db_type}_{hash(connection_string) % 10000}.json"
            
            # Store as resource (we'll need to integrate with ResourceManager)
            # For now, return the schema data with the URI
            result = {
                "schema_uri": schema_uri,
                "database_type": db_type,
                "table_count": len(table_names),
                "status": "discovered",
                "schema_data": schema_data
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "status": "failed"
            }, indent=2)
    
    def _extract_schema_from_text(self, schema_text: str) -> Dict[str, Any]:
        """Extract schema information from formatted text when JSON parsing fails."""
        schema_data = {
            "database_type": "unknown",
            "tables": {},
            "relationships": []
        }
        
        try:
            lines = schema_text.split('\n')
            current_table = None
            in_columns_section = False
            
            for line in lines:
                line = line.strip()
                
                # Extract database type
                if "Database Type:" in line:
                    schema_data["database_type"] = line.split("Database Type:")[1].strip()
                
                # Extract table name
                elif line.startswith("## Table:"):
                    table_name = line.split("## Table:")[1].strip()
                    current_table = table_name
                    in_columns_section = False
                    schema_data["tables"][table_name] = {
                        "columns": [],
                        "foreign_keys": []
                    }
                
                # Start of columns section
                elif line == "**Columns:**" and current_table:
                    in_columns_section = True
                
                # Extract column information
                elif line.startswith("- ") and current_table and in_columns_section and ":" in line:
                    # Format: "- column_name: column_type (PRIMARY KEY)"
                    col_info = line[2:].split(":")
                    if len(col_info) >= 2:
                        col_name = col_info[0].strip()
                        col_type_part = col_info[1].strip()
                        
                        # Extract type and check for primary key
                        is_primary_key = "(PRIMARY KEY)" in col_type_part
                        col_type = col_type_part.replace("(PRIMARY KEY)", "").strip()
                        
                        schema_data["tables"][current_table]["columns"].append({
                            "name": col_name,
                            "type": col_type,
                            "primary_key": is_primary_key
                        })
                
                # End of columns section (empty line or new section)
                elif line == "" and in_columns_section:
                    in_columns_section = False
                
                # Extract relationships
                elif line.startswith("- ") and "->" in line and "Table Relationships" in schema_text:
                    # Format: "- table.column -> referenced_table.referenced_column"
                    rel_parts = line[2:].split("->")
                    if len(rel_parts) == 2:
                        left_side = rel_parts[0].strip()
                        right_side = rel_parts[1].strip()
                        
                        if "." in left_side and "." in right_side:
                            left_parts = left_side.split(".")
                            right_parts = right_side.split(".")
                            
                            if len(left_parts) == 2 and len(right_parts) == 2:
                                schema_data["relationships"].append({
                                    "table": left_parts[0].strip(),
                                    "column": left_parts[1].strip(),
                                    "references": right_side
                                })
            
            print(f"📋 Extracted schema: {len(schema_data['tables'])} tables, {len(schema_data['relationships'])} relationships")
            return schema_data
            
        except Exception as e:
            print(f"Error extracting schema from text: {e}")
            return schema_data 