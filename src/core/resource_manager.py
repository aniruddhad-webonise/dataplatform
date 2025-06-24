"""
Resource Manager for the MCP server.
Handles storage and retrieval of tables, charts, and other resources.
"""

import json
import os
import uuid
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
    
    async def store_table_resource(self, table_data: Dict[str, Any], sql_query: str) -> str:
        """Store table data as a resource and return the URI."""
        try:
            # Generate unique URI
            resource_id = str(uuid.uuid4())
            uri = f"resource://tables/{resource_id}"
            
            # Create resource metadata
            metadata = {
                "uri": uri,
                "type": "table",
                "sql_query": sql_query,
                "columns": table_data.get("columns", []),
                "row_count": table_data.get("row_count", 0),
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=self.expiry_hours)).isoformat()
            }
            
            # Store the resource data
            resource_file = self.storage_path / f"tables/{resource_id}.json"
            resource_file.parent.mkdir(exist_ok=True)
            
            with open(resource_file, 'w') as f:
                json.dump(table_data, f, indent=2, default=str)
            
            # Update metadata
            self.resources[uri] = metadata
            self._save_metadata()
            
            return uri
            
        except Exception as e:
            print(f"Error storing table resource: {e}")
            return None
    
    async def store_chart_resource(self, chart_data: Dict[str, Any], chart_type: str) -> str:
        """Store chart data as a resource and return the URI."""
        try:
            # Generate unique URI
            resource_id = str(uuid.uuid4())
            uri = f"resource://charts/{resource_id}"
            
            # Create resource metadata
            metadata = {
                "uri": uri,
                "type": "chart",
                "chart_type": chart_type,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=self.expiry_hours)).isoformat()
            }
            
            # Store the resource data
            resource_file = self.storage_path / f"charts/{resource_id}.json"
            resource_file.parent.mkdir(exist_ok=True)
            
            with open(resource_file, 'w') as f:
                json.dump(chart_data, f, indent=2, default=str)
            
            # Update metadata
            self.resources[uri] = metadata
            self._save_metadata()
            
            return uri
            
        except Exception as e:
            print(f"Error storing chart resource: {e}")
            return None
    
    async def store_ml_resource(self, ml_data: Dict[str, Any], ml_type: str) -> str:
        """Store ML results as a resource and return the URI."""
        try:
            # Generate unique URI
            resource_id = str(uuid.uuid4())
            uri = f"resource://ml/{resource_id}"
            
            # Create resource metadata
            metadata = {
                "uri": uri,
                "type": "ml",
                "ml_type": ml_type,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=self.expiry_hours)).isoformat()
            }
            
            # Store the resource data
            resource_file = self.storage_path / f"ml/{resource_id}.json"
            resource_file.parent.mkdir(exist_ok=True)
            
            with open(resource_file, 'w') as f:
                json.dump(ml_data, f, indent=2, default=str)
            
            # Update metadata
            self.resources[uri] = metadata
            self._save_metadata()
            
            return uri
            
        except Exception as e:
            print(f"Error storing ML resource: {e}")
            return None
    
    async def store_schema_resource(self, schema_data: Dict[str, Any], schema_uri: str) -> str:
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
            
            # Create resource metadata
            metadata = {
                "uri": internal_uri,
                "type": "schema",
                "database_type": schema_data.get("database_type", "unknown"),
                "table_count": len(schema_data.get("tables", {})),
                "connection_string": schema_data.get("connection_string", ""),
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=self.expiry_hours)).isoformat()
            }
            
            # Store the schema data
            resource_file = self.storage_path / f"schemas/{internal_uri.split('/')[-1]}"
            resource_file.parent.mkdir(exist_ok=True)
            
            with open(resource_file, 'w') as f:
                json.dump(schema_data, f, indent=2, default=str)
            
            # Update metadata
            self.resources[internal_uri] = metadata
            self._save_metadata()
            
            return internal_uri
            
        except Exception as e:
            print(f"Error storing schema resource: {e}")
            return None
    
    async def list_resources(self) -> List[Resource]:
        """List all available resources."""
        try:
            # Cleanup expired resources first
            self._cleanup_expired_resources()
            
            resources = []
            for uri, metadata in self.resources.items():
                resource = Resource(
                    uri=uri,
                    name=metadata.get("type", "unknown"),
                    description=f"{metadata.get('type', 'Unknown')} resource created at {metadata.get('created_at', 'unknown')}",
                    mimeType="application/json"
                )
                resources.append(resource)
            
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
        columns = data.get("columns", [])
        rows = data.get("data", [])
        row_count = data.get("row_count", 0)
        sql_query = metadata.get("sql_query", "Unknown")
        
        # Create a formatted table
        formatted = f"# Table Resource: {metadata['uri']}\n\n"
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
        chart_type = metadata.get("chart_type", "unknown")
        
        formatted = f"# Chart Resource: {metadata['uri']}\n\n"
        formatted += f"**Chart Type:** {chart_type}\n\n"
        formatted += f"**Chart Data:**\n```json\n{json.dumps(data, indent=2)}\n```\n"
        
        return formatted
    
    def _format_ml_resource(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Format ML resource for display."""
        ml_type = metadata.get("ml_type", "unknown")
        
        formatted = f"# ML Resource: {metadata['uri']}\n\n"
        formatted += f"**ML Type:** {ml_type}\n\n"
        formatted += f"**Results:**\n```json\n{json.dumps(data, indent=2)}\n```\n"
        
        return formatted
    
    def _format_schema_resource(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Format schema resource for display."""
        database_type = data.get("database_type", "unknown")
        tables = data.get("tables", {})
        relationships = data.get("relationships", [])
        
        formatted = f"# Database Schema Resource: {metadata['uri']}\n\n"
        formatted += f"**Database Type:** {database_type}\n\n"
        formatted += f"**Connection String:** {data.get('connection_string', 'N/A')}\n\n"
        formatted += f"**Tables:** {len(tables)}\n\n"
        
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