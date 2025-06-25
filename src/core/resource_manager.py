"""
Resource Manager for the MCP server.
Handles storage and retrieval of tables, charts, and other resources.
"""

import json
import os
import uuid
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from mcp.types import Resource, TextContent, ImageContent, EmbeddedResource

class ResourceManager:
    """Manages resources (tables, charts, ML results) for the MCP server."""
    
    def __init__(self):
        self.storage_path = Path(os.getenv("RESOURCE_STORAGE_PATH", "./data/resources"))
        self.expiry_hours = int(os.getenv("RESOURCE_EXPIRY_HOURS", "24"))
        self.resources: Dict[str, Dict[str, Any]] = {}
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing resources
        self._load_resources()
    
    def _load_resources(self):
        """Load existing resources from storage."""
        try:
            metadata_file = self.storage_path / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.resources = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load resource metadata: {e}")
            self.resources = {}
    
    def _save_metadata(self):
        """Save resource metadata to storage."""
        try:
            metadata_file = self.storage_path / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(self.resources, f, indent=2, default=str)
        except Exception as e:
            print(f"Warning: Could not save resource metadata: {e}")
    
    def _cleanup_expired_resources(self):
        """Remove expired resources."""
        current_time = datetime.now()
        expired_uris = []
        
        for uri, metadata in self.resources.items():
            created_time = datetime.fromisoformat(metadata.get("created_at", "1970-01-01T00:00:00"))
            if current_time - created_time > timedelta(hours=self.expiry_hours):
                expired_uris.append(uri)
        
        for uri in expired_uris:
            self._delete_resource(uri)
    
    def _delete_resource(self, uri: str):
        """Delete a specific resource."""
        if uri in self.resources:
            metadata = self.resources[uri]
            resource_type = metadata.get("type", "unknown")
            
            # Determine the correct file path based on resource type
            resource_id = uri.split("/")[-1]
            
            if resource_type == "schema":
                # Schema files already have .json extension in the URI
                resource_file = self.storage_path / f"schemas/{resource_id}"
            else:
                # Other resource types need .json added
                resource_file = self.storage_path / f"{resource_type}s/{resource_id}.json"
            
            # Delete the resource file
            if resource_file.exists():
                resource_file.unlink()
                print(f"🗑️  Deleted file: {resource_file}")
            else:
                print(f"⚠️  File not found: {resource_file}")
            
            # Remove from metadata
            del self.resources[uri]
            self._save_metadata()
    
    async def store_table_resource(self, table_data: Dict[str, Any], sql_query: str, 
                                 name: str = None, description: str = None, 
                                 tags: List[str] = None, category: str = None,
                                 source_schema: str = None) -> str:
        """Store table data as a resource and return the URI."""
        try:
            # Generate unique URI
            resource_id = str(uuid.uuid4())
            uri = f"resource://tables/{resource_id}"
            
            # Prepare content for metadata generation
            content = {
                "sql_query": sql_query,
                "columns": table_data.get("columns", []),
                "row_count": table_data.get("row_count", 0)
            }
            
            # Create enhanced metadata
            metadata = self._create_enhanced_metadata(
                uri=uri,
                resource_type="table",
                content=content,
                custom_name=name,
                custom_description=description,
                custom_tags=tags,
                custom_category=category,
                sql_query=sql_query,
                columns=table_data.get("columns", []),
                row_count=table_data.get("row_count", 0),
                source_schema=source_schema
            )
            
            # Store the resource data
            resource_file = self.storage_path / f"tables/{resource_id}.json"
            resource_file.parent.mkdir(exist_ok=True)
            
            with open(resource_file, 'w') as f:
                json.dump(table_data, f, indent=2, default=str)
            
            # Update metadata
            self.resources[uri] = metadata
            self._save_metadata()
            
            print(f"📊 Stored enhanced table resource: {metadata['name']} (tags: {', '.join(metadata['tags'])})")
            return uri
            
        except Exception as e:
            print(f"Error storing table resource: {e}")
            return None
    
    async def store_chart_resource(self, chart_data: Dict[str, Any], chart_type: str,
                                 name: str = None, description: str = None,
                                 tags: List[str] = None, category: str = None) -> str:
        """Store chart data as a resource and return the URI."""
        try:
            # Generate unique URI
            resource_id = str(uuid.uuid4())
            uri = f"resource://charts/{resource_id}"
            
            # Prepare content for metadata generation
            content = {
                "chart_type": chart_type
            }
            
            # Create enhanced metadata
            metadata = self._create_enhanced_metadata(
                uri=uri,
                resource_type="chart",
                content=content,
                custom_name=name,
                custom_description=description,
                custom_tags=tags,
                custom_category=category,
                chart_type=chart_type
            )
            
            # Store the resource data
            resource_file = self.storage_path / f"charts/{resource_id}.json"
            resource_file.parent.mkdir(exist_ok=True)
            
            with open(resource_file, 'w') as f:
                json.dump(chart_data, f, indent=2, default=str)
            
            # Update metadata
            self.resources[uri] = metadata
            self._save_metadata()
            
            print(f"📈 Stored enhanced chart resource: {metadata['name']} (tags: {', '.join(metadata['tags'])})")
            return uri
            
        except Exception as e:
            print(f"Error storing chart resource: {e}")
            return None
    
    async def store_ml_resource(self, ml_data: Dict[str, Any], ml_type: str,
                              name: str = None, description: str = None,
                              tags: List[str] = None, category: str = None) -> str:
        """Store ML results as a resource and return the URI."""
        try:
            # Generate unique URI
            resource_id = str(uuid.uuid4())
            uri = f"resource://ml/{resource_id}"
            
            # Prepare content for metadata generation
            content = {
                "ml_type": ml_type
            }
            
            # Create enhanced metadata
            metadata = self._create_enhanced_metadata(
                uri=uri,
                resource_type="ml",
                content=content,
                custom_name=name,
                custom_description=description,
                custom_tags=tags,
                custom_category=category,
                ml_type=ml_type
            )
            
            # Store the resource data
            resource_file = self.storage_path / f"ml/{resource_id}.json"
            resource_file.parent.mkdir(exist_ok=True)
            
            with open(resource_file, 'w') as f:
                json.dump(ml_data, f, indent=2, default=str)
            
            # Update metadata
            self.resources[uri] = metadata
            self._save_metadata()
            
            print(f"🤖 Stored enhanced ML resource: {metadata['name']} (tags: {', '.join(metadata['tags'])})")
            return uri
            
        except Exception as e:
            print(f"Error storing ML resource: {e}")
            return None
    
    async def store_schema_resource(self, schema_data: Dict[str, Any], schema_uri: str,
                                  name: str = None, description: str = None,
                                  tags: List[str] = None, category: str = None) -> str:
        """Store database schema as a resource and return the URI."""
        try:
            # Convert schema_uri to internal resource URI format
            if schema_uri.startswith("mcp://"):
                # Extract the last part of the mcp URI
                resource_id = schema_uri.split("/")[-1]
                internal_uri = f"resource://schemas/{resource_id}.json"
            else:
                # Use the provided schema URI or generate one
                if not schema_uri:
                    resource_id = str(uuid.uuid4())
                    internal_uri = f"resource://schemas/{resource_id}.json"
                else:
                    internal_uri = schema_uri
            
            # Prepare content for metadata generation
            content = {
                "database_type": schema_data.get("database_type", "unknown"),
                "tables": schema_data.get("tables", {}),
                "connection_string": schema_data.get("connection_string", "")
            }
            
            # Create enhanced metadata
            metadata = self._create_enhanced_metadata(
                uri=internal_uri,
                resource_type="schema",
                content=content,
                custom_name=name,
                custom_description=description,
                custom_tags=tags,
                custom_category=category,
                database_type=schema_data.get("database_type", "unknown"),
                table_count=len(schema_data.get("tables", {})),
                connection_string=schema_data.get("connection_string", "")
            )
            
            # Store the schema data
            resource_file = self.storage_path / f"schemas/{internal_uri.split('/')[-1]}"
            resource_file.parent.mkdir(exist_ok=True)
            
            with open(resource_file, 'w') as f:
                json.dump(schema_data, f, indent=2, default=str)
            
            # Update metadata
            self.resources[internal_uri] = metadata
            self._save_metadata()
            
            print(f"🗄️ Stored enhanced schema resource: {metadata['name']} (tags: {', '.join(metadata['tags'])})")
            return internal_uri
            
        except Exception as e:
            print(f"Error storing schema resource: {e}")
            return None
    
    async def list_resources(self) -> List[Resource]:
        """List all available resources."""
        try:
            print(f"🔍 Listing resources. Current resources count: {len(self.resources)}")
            
            # Cleanup expired resources first
            self._cleanup_expired_resources()
            
            print(f"🔍 After cleanup. Resources count: {len(self.resources)}")
            
            resources = []
            for uri, metadata in self.resources.items():
                print(f"🔍 Processing resource: {uri}")
                # Use enhanced metadata for better descriptions
                name = metadata.get("name", metadata.get("type", "unknown"))
                description = metadata.get("description", f"{metadata.get('type', 'Unknown')} resource")
                tags = metadata.get("tags", [])
                category = metadata.get("category", "general")
                
                # Create enhanced description with tags and category
                enhanced_description = f"{description} | Category: {category} | Tags: {', '.join(tags)}"
                
                resource = Resource(
                    uri=uri,
                    name=name,
                    description=enhanced_description,
                    mimeType="application/json"
                )
                resources.append(resource)
            
            print(f"🔍 Returning {len(resources)} resources")
            return resources
            
        except Exception as e:
            print(f"Error listing resources: {e}")
            return []
    
    async def read_resource(self, uri: str, raw: bool = False) -> List[TextContent | ImageContent | EmbeddedResource]:
        """Read a specific resource."""
        try:
            if uri not in self.resources:
                return [TextContent(type="text", text=f"Resource not found: {uri}")]
            
            metadata = self.resources[uri]
            resource_type = metadata.get("type", "unknown")
            
            # Update access tracking
            metadata["access_count"] = metadata.get("access_count", 0) + 1
            metadata["last_accessed"] = datetime.now().isoformat()
            self._save_metadata()
            
            # Determine the file path
            resource_id = uri.split("/")[-1]
            
            # Handle different resource types
            if resource_type == "schema":
                # Schema files already have .json extension
                resource_file = self.storage_path / f"schemas/{resource_id}"
            else:
                # Other resource types need .json added
                resource_file = self.storage_path / f"{resource_type}s/{resource_id}.json"
            
            if not resource_file.exists():
                return [TextContent(type="text", text=f"Resource file not found: {uri} (path: {resource_file})")]
            
            # Read the resource data
            with open(resource_file, 'r') as f:
                data = json.load(f)
            
            # If raw is requested, return the JSON data directly
            if raw:
                return [TextContent(type="text", text=json.dumps(data, indent=2))]
            
            # Format the response based on resource type
            if resource_type == "table":
                response = self._format_table_resource(data, metadata)
            elif resource_type == "chart":
                response = self._format_chart_resource(data, metadata)
            elif resource_type == "ml":
                response = self._format_ml_resource(data, metadata)
            elif resource_type == "schema":
                response = self._format_schema_resource(data, metadata)
            else:
                response = f"Unknown resource type: {resource_type}"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error reading resource: {str(e)}")]
    
    def _format_table_resource(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Format table resource for display."""
        # Get enhanced metadata
        name = metadata.get("name", "Unknown Table")
        description = metadata.get("description", "No description available")
        tags = metadata.get("tags", [])
        category = metadata.get("category", "general")
        access_count = metadata.get("access_count", 0)
        last_accessed = metadata.get("last_accessed", "Never")
        
        # Get type-specific metadata
        type_metadata = metadata.get("metadata", {})
        sql_query = type_metadata.get("sql_query", "Unknown")
        columns = type_metadata.get("columns", [])
        row_count = type_metadata.get("row_count", 0)
        source_schema = type_metadata.get("source_schema", "None")
        
        rows = data.get("data", [])
        
        # Create a formatted table
        formatted = f"# {name}\n\n"
        formatted += f"**Description:** {description}\n\n"
        formatted += f"**Category:** {category}\n\n"
        formatted += f"**Tags:** {', '.join(tags)}\n\n"
        formatted += f"**Access Count:** {access_count}\n\n"
        formatted += f"**Last Accessed:** {last_accessed}\n\n"
        formatted += f"**Source Schema:** {source_schema}\n\n"
        formatted += f"**SQL Query:** `{sql_query}`\n\n"
        formatted += f"**Columns:** {', '.join(columns)}\n\n"
        formatted += f"**Row Count:** {row_count}\n\n"
        
        if rows:
            # Show first few rows as example
            formatted += "**Sample Data:**\n"
            formatted += "| " + " | ".join(columns) + " |\n"
            formatted += "| " + " | ".join(["---"] * len(columns)) + " |\n"
            
            for row in rows[:5]:  # Show first 5 rows
                formatted += "| " + " | ".join([str(row.get(col, "")) for col in columns]) + " |\n"
            
            if len(rows) > 5:
                formatted += f"\n*... and {len(rows) - 5} more rows*\n"
        
        return formatted
    
    def _format_chart_resource(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Format chart resource for display."""
        # Get enhanced metadata
        name = metadata.get("name", "Unknown Chart")
        description = metadata.get("description", "No description available")
        tags = metadata.get("tags", [])
        category = metadata.get("category", "general")
        access_count = metadata.get("access_count", 0)
        last_accessed = metadata.get("last_accessed", "Never")
        
        # Get type-specific metadata
        type_metadata = metadata.get("metadata", {})
        chart_type = type_metadata.get("chart_type", "unknown")
        
        formatted = f"# {name}\n\n"
        formatted += f"**Description:** {description}\n\n"
        formatted += f"**Category:** {category}\n\n"
        formatted += f"**Tags:** {', '.join(tags)}\n\n"
        formatted += f"**Access Count:** {access_count}\n\n"
        formatted += f"**Last Accessed:** {last_accessed}\n\n"
        formatted += f"**Chart Type:** {chart_type}\n\n"
        formatted += f"**Chart Data:**\n```json\n{json.dumps(data, indent=2)}\n```\n"
        
        return formatted
    
    def _format_ml_resource(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Format ML resource for display."""
        # Get enhanced metadata
        name = metadata.get("name", "Unknown ML Resource")
        description = metadata.get("description", "No description available")
        tags = metadata.get("tags", [])
        category = metadata.get("category", "general")
        access_count = metadata.get("access_count", 0)
        last_accessed = metadata.get("last_accessed", "Never")
        
        # Get type-specific metadata
        type_metadata = metadata.get("metadata", {})
        ml_type = type_metadata.get("ml_type", "unknown")
        
        formatted = f"# {name}\n\n"
        formatted += f"**Description:** {description}\n\n"
        formatted += f"**Category:** {category}\n\n"
        formatted += f"**Tags:** {', '.join(tags)}\n\n"
        formatted += f"**Access Count:** {access_count}\n\n"
        formatted += f"**Last Accessed:** {last_accessed}\n\n"
        formatted += f"**ML Type:** {ml_type}\n\n"
        formatted += f"**Results:**\n```json\n{json.dumps(data, indent=2)}\n```\n"
        
        return formatted
    
    def _format_schema_resource(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Format schema resource for display."""
        # Get enhanced metadata
        name = metadata.get("name", "Unknown Schema")
        description = metadata.get("description", "No description available")
        tags = metadata.get("tags", [])
        category = metadata.get("category", "general")
        access_count = metadata.get("access_count", 0)
        last_accessed = metadata.get("last_accessed", "Never")
        
        # Get type-specific metadata
        type_metadata = metadata.get("metadata", {})
        database_type = type_metadata.get("database_type", "unknown")
        table_count = type_metadata.get("table_count", 0)
        connection_string = type_metadata.get("connection_string", "N/A")
        
        tables = data.get("tables", {})
        relationships = data.get("relationships", [])
        
        formatted = f"# {name}\n\n"
        formatted += f"**Description:** {description}\n\n"
        formatted += f"**Category:** {category}\n\n"
        formatted += f"**Tags:** {', '.join(tags)}\n\n"
        formatted += f"**Access Count:** {access_count}\n\n"
        formatted += f"**Last Accessed:** {last_accessed}\n\n"
        formatted += f"**Database Type:** {database_type}\n\n"
        formatted += f"**Connection String:** {connection_string}\n\n"
        formatted += f"**Tables:** {table_count}\n\n"
        
        # Show table information
        for table_name, table_info in tables.items():
            formatted += f"## Table: {table_name}\n\n"
            
            # Columns
            columns = table_info.get("columns", [])
            formatted += "**Columns:**\n"
            for col in columns:
                pk_marker = " (PRIMARY KEY)" if col.get("primary_key") else ""
                formatted += f"- {col['name']}: {col['type']}{pk_marker}\n"
            
            # Foreign keys
            foreign_keys = table_info.get("foreign_keys", [])
            if foreign_keys:
                formatted += "\n**Foreign Keys:**\n"
                for fk in foreign_keys:
                    formatted += f"- {fk['column']} -> {fk['references_table']}.{fk['references_column']}\n"
            
            formatted += "\n"
        
        # Show relationships
        if relationships:
            formatted += "## Table Relationships\n\n"
            for rel in relationships:
                formatted += f"- {rel['table']}.{rel['column']} -> {rel['references']}\n"
        
        return formatted
    
    def _generate_resource_name(self, resource_type: str, content: Dict[str, Any]) -> str:
        """Auto-generate a human-readable name for a resource."""
        if resource_type == "table":
            sql_query = content.get("sql_query", "")
            if sql_query:
                # Extract table name or create descriptive name from SQL
                if "FROM" in sql_query.upper():
                    # Try to extract table name
                    match = re.search(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
                    if match:
                        table_name = match.group(1)
                        return f"{table_name.title()} Query Results"
                
                # Create name from query type
                if "SELECT" in sql_query.upper():
                    if "COUNT" in sql_query.upper():
                        return "Count Query Results"
                    elif "SUM" in sql_query.upper() or "AVG" in sql_query.upper():
                        return "Aggregation Query Results"
                    else:
                        return "Data Query Results"
            
            return "Table Resource"
        
        elif resource_type == "schema":
            db_type = content.get("database_type", "unknown")
            table_count = len(content.get("tables", {}))
            return f"{db_type.title()} Database Schema ({table_count} tables)"
        
        elif resource_type == "chart":
            chart_type = content.get("chart_type", "unknown")
            return f"{chart_type.title()} Chart"
        
        elif resource_type == "ml":
            ml_type = content.get("ml_type", "unknown")
            return f"{ml_type.title()} Model Results"
        
        return f"{resource_type.title()} Resource"
    
    def _generate_resource_description(self, resource_type: str, content: Dict[str, Any]) -> str:
        """Auto-generate a description for a resource."""
        if resource_type == "table":
            sql_query = content.get("sql_query", "")
            row_count = content.get("row_count", 0)
            columns = content.get("columns", [])
            
            desc = f"Query results with {row_count} rows"
            if columns:
                desc += f" and {len(columns)} columns: {', '.join(columns[:3])}"
                if len(columns) > 3:
                    desc += f" and {len(columns) - 3} more"
            
            if sql_query:
                desc += f". Generated from SQL: {sql_query[:100]}"
                if len(sql_query) > 100:
                    desc += "..."
            
            return desc
        
        elif resource_type == "schema":
            db_type = content.get("database_type", "unknown")
            tables = content.get("tables", {})
            table_names = list(tables.keys())[:3]
            
            desc = f"{db_type.title()} database schema with {len(tables)} tables"
            if table_names:
                desc += f" including: {', '.join(table_names)}"
                if len(tables) > 3:
                    desc += f" and {len(tables) - 3} more"
            
            return desc
        
        elif resource_type == "chart":
            chart_type = content.get("chart_type", "unknown")
            return f"{chart_type.title()} visualization chart"
        
        elif resource_type == "ml":
            ml_type = content.get("ml_type", "unknown")
            return f"{ml_type.title()} machine learning model results"
        
        return f"{resource_type.title()} resource"
    
    def _generate_resource_tags(self, resource_type: str, content: Dict[str, Any]) -> List[str]:
        """Auto-generate tags for a resource."""
        tags = [resource_type]
        
        if resource_type == "table":
            sql_query = content.get("sql_query", "").lower()
            columns = [col.lower() for col in content.get("columns", [])]
            
            # Add tags based on SQL keywords
            if "select" in sql_query:
                tags.append("query")
            if "join" in sql_query:
                tags.append("join")
            if "group by" in sql_query:
                tags.append("aggregation")
            if "order by" in sql_query:
                tags.append("sorted")
            if "limit" in sql_query:
                tags.append("limited")
            
            # Add tags based on column names
            for col in columns:
                if "id" in col:
                    tags.append("identifier")
                if "name" in col:
                    tags.append("name")
                if "date" in col or "time" in col:
                    tags.append("temporal")
                if "amount" in col or "price" in col or "cost" in col:
                    tags.append("financial")
                if "count" in col or "total" in col:
                    tags.append("metrics")
            
            # Remove duplicates
            tags = list(set(tags))
        
        elif resource_type == "schema":
            db_type = content.get("database_type", "unknown")
            tags.append(db_type)
            tags.append("schema")
            
            tables = content.get("tables", {})
            if tables:
                tags.append("structured")
        
        elif resource_type == "chart":
            chart_type = content.get("chart_type", "unknown")
            tags.append(chart_type)
            tags.append("visualization")
        
        elif resource_type == "ml":
            ml_type = content.get("ml_type", "unknown")
            tags.append(ml_type)
            tags.append("machine-learning")
        
        return tags
    
    def _determine_resource_category(self, resource_type: str, content: Dict[str, Any]) -> str:
        """Determine the category for a resource."""
        if resource_type == "schema":
            return "infrastructure"
        elif resource_type == "table":
            return "data"
        elif resource_type == "chart":
            return "visualization"
        elif resource_type == "ml":
            return "analytics"
        else:
            return "general"
    
    def _create_enhanced_metadata(self, uri: str, resource_type: str, content: Dict[str, Any], 
                                custom_name: str = None, custom_description: str = None, 
                                custom_tags: List[str] = None, custom_category: str = None,
                                **type_specific_metadata) -> Dict[str, Any]:
        """Create enhanced metadata for a resource."""
        
        # Auto-generate basic fields if not provided
        name = custom_name or self._generate_resource_name(resource_type, content)
        description = custom_description or self._generate_resource_description(resource_type, content)
        tags = custom_tags or self._generate_resource_tags(resource_type, content)
        category = custom_category or self._determine_resource_category(resource_type, content)
        
        # Create enhanced metadata structure
        metadata = {
            "uri": uri,
            "type": resource_type,
            "name": name,
            "description": description,
            "tags": tags,
            "category": category,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=self.expiry_hours)).isoformat(),
            "access_count": 0,
            "last_accessed": None,
            "metadata": {
                **type_specific_metadata
            }
        }
        
        return metadata 