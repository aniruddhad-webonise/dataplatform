#!/usr/bin/env python3
"""
HTTP Server wrapper for the Advanced MCP SQL Analytics Server.
Provides REST endpoints for testing with Postman while maintaining MCP functionality.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from aiohttp import web
import uuid
import urllib.parse

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from core.sql_tools import SQLTools
from core.resource_manager import ResourceManager
from core.prompt_manager import PromptManager
from core.tool_loader import ToolLoader
from core.sql_explanation_helper import SQLExplanationHelper
from core.search_service import SearchService

# Load environment variables
load_dotenv()

class HTTPMCPServer:
    """HTTP wrapper for the MCP server with REST endpoints."""
    
    def __init__(self):
        self.sql_tools = SQLTools()
        self.resource_manager = ResourceManager()
        self.prompt_manager = PromptManager()
        self.tool_loader = ToolLoader()
        self.sql_explanation_helper = SQLExplanationHelper()
        self.search_service = SearchService(self.resource_manager)
        
        # Load tools from XML files
        self.tools = self.tool_loader.load_all_tools()
        self.active_connections = {}
        
        print(f"Loaded {len(self.tools)} tools:")
        for tool in self.tools:
            print(f"  - {tool.name}: {tool.description}")
    
    async def handle_tool_call(self, request):
        """Handle tool call requests via HTTP POST."""
        try:
            data = await request.json()
            tool_name = data.get("name")
            arguments = data.get("arguments", {})
            
            if tool_name == "generate_sql":
                result = await self.sql_tools.generate_sql(
                    arguments.get("nl_query"),
                    arguments.get("db_type", "postgresql"),
                    arguments.get("schema_uri")
                )
                
                result_data = json.loads(result)
                
                # Generate explanation if requested
                if arguments.get("include_explanation", False):
                    sql_query = result_data.get("sql_query")
                    if sql_query:
                        explanation = await self.sql_explanation_helper.generate_explanation(
                            sql_query, 
                            arguments.get("target_audience", "business_user")
                        )
                        result_data["explanation"] = explanation
                        result = json.dumps(result_data, indent=2)
                
                return web.json_response({
                    "status": "success",
                    "tool": tool_name,
                    "result": json.loads(result)
                })
            
            elif tool_name == "validate_sql":
                result = await self.sql_tools.validate_sql(
                    arguments.get("sql_query")
                )
                return web.json_response({
                    "status": "success",
                    "tool": tool_name,
                    "result": json.loads(result)
                })
            
            elif tool_name == "execute_sql":
                result = await self.sql_tools.execute_sql(
                    arguments.get("sql_query"),
                    arguments.get("db_connection", "sqlite:///./data/analytics.db"),
                    arguments.get("store_as_resource", True),
                    arguments.get("resource_name"),
                    arguments.get("resource_description"),
                    arguments.get("resource_tags"),
                    arguments.get("resource_category"),
                    arguments.get("max_rows", 1000)
                )
                
                return web.json_response({
                    "status": "success",
                    "tool": tool_name,
                    "result": json.loads(result)
                })
            
            elif tool_name == "discover_schema":
                result = await self.sql_tools.discover_schema(
                    arguments.get("connection_string"),
                    arguments.get("include_sample_data", True),
                    arguments.get("max_sample_rows", 5),
                    arguments.get("schema_name"),
                    arguments.get("schema_description"),
                    arguments.get("schema_tags"),
                    arguments.get("schema_category")
                )
                
                return web.json_response({
                    "status": "success",
                    "tool": tool_name,
                    "result": json.loads(result)
                })
            
            elif tool_name == "search_resources":
                result = self.search_service.search_resources(
                    query=arguments.get("query"),
                    tags=arguments.get("tags"),
                    any_tags=arguments.get("any_tags"),
                    category=arguments.get("category"),
                    resource_type=arguments.get("resource_type"),
                    created_after=arguments.get("created_after"),
                    created_before=arguments.get("created_before"),
                    min_access_count=arguments.get("min_access_count", 0),
                    limit=arguments.get("limit", 50),
                    sort_by=arguments.get("sort_by", "created_at"),
                    sort_order=arguments.get("sort_order", "desc")
                )
                
                return web.json_response({
                    "status": "success",
                    "tool": tool_name,
                    "result": result
                })
            
            elif tool_name == "create_viz":
                return web.json_response({
                    "status": "not_implemented",
                    "tool": tool_name,
                    "message": "Visualization tool will be implemented in Day 3"
                })
            
            elif tool_name == "predictive_model":
                return web.json_response({
                    "status": "not_implemented",
                    "tool": tool_name,
                    "message": "Predictive model tool will be implemented in Day 4"
                })
            
            else:
                return web.json_response({
                    "status": "error",
                    "error": f"Unknown tool: {tool_name}"
                }, status=400)
                
        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def handle_list_tools(self, request):
        """List all available tools."""
        tools_data = []
        for tool in self.tools:
            tools_data.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema.get("properties", {}),
                "required": tool.inputSchema.get("required", [])
            })
        
        return web.json_response({
            "status": "success",
            "tools": tools_data
        })
    
    async def handle_list_resources(self, request):
        """List all available resources."""
        resources = await self.resource_manager.list_resources()
        resources_data = []
        for resource in resources:
            resources_data.append({
                "uri": str(resource.uri),
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mimeType
            })
        
        return web.json_response({
            "status": "success",
            "resources": resources_data
        })
    
    async def handle_search_resources(self, request):
        """Search resources with query parameters."""
        try:
            # Get query parameters
            query = request.query.get("q")
            tags = request.query.get("tags")
            any_tags = request.query.get("any_tags")
            category = request.query.get("category")
            resource_type = request.query.get("type")
            limit = int(request.query.get("limit", 50))
            
            # Parse tags from comma-separated string
            if tags:
                tags = [tag.strip() for tag in tags.split(",")]
            if any_tags:
                any_tags = [tag.strip() for tag in any_tags.split(",")]
            
            result = self.search_service.search_resources(
                query=query,
                tags=tags,
                any_tags=any_tags,
                category=category,
                resource_type=resource_type,
                limit=limit
            )
            
            return web.json_response(result)
            
        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def handle_popular_resources(self, request):
        """Get most frequently accessed resources."""
        try:
            limit = int(request.query.get("limit", 10))
            result = self.search_service.get_popular_resources(limit)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def handle_recent_resources(self, request):
        """Get recently created resources."""
        try:
            limit = int(request.query.get("limit", 10))
            result = self.search_service.get_recent_resources(limit)
            return web.json_response(result)
        except Exception as e:
            return web.json_response({
                "status": "error",
                "error": str(e)
            }, status=500)
    
    async def handle_read_resource(self, request):
        """Read a specific resource."""
        uri = request.match_info.get("uri")
        if not uri:
            return web.json_response({
                "status": "error",
                "error": "Resource URI is required"
            }, status=400)
        
        # URL decode the URI to handle special characters
        decoded_uri = urllib.parse.unquote(uri)
        
        print(f"🔍 Reading resource: {decoded_uri}")
        
        content = await self.resource_manager.read_resource(decoded_uri)
        return web.json_response({
            "status": "success",
            "uri": decoded_uri,
            "content": content[0].text if content else ""
        })
    
    async def handle_list_prompts(self, request):
        """List all available prompts."""
        prompts = await self.prompt_manager.list_prompts()
        return web.json_response({
            "status": "success",
            "prompts": prompts
        })
    
    async def handle_get_prompt(self, request):
        """Get a specific prompt template."""
        name = request.match_info.get("name")
        if not name:
            return web.json_response({
                "status": "error",
                "error": "Prompt name is required"
            }, status=400)
        
        prompt_content = await self.prompt_manager.get_prompt(name)
        return web.json_response({
            "status": "success",
            "name": name,
            "content": prompt_content
        })
    
    async def sse_handler(self, request):
        """Handle Server-Sent Events for real-time updates."""
        connection_id = str(uuid.uuid4())
        response = web.StreamResponse(
            status=200,
            reason='OK',
            headers={
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            }
        )
        await response.prepare(request)
        
        # Store the connection
        self.active_connections[connection_id] = response
        
        try:
            # Send initial tools list
            tools_data = {
                'type': 'tools',
                'tools': [
                    {
                        'name': t.name,
                        'description': t.description,
                        'parameters': t.inputSchema.get("properties", {})
                    } for t in self.tools
                ]
            }
            await response.write(f"data: {json.dumps(tools_data)}\n\n".encode())
            
            # Keep the connection alive
            while True:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                await response.write(f"data: {json.dumps({'type': 'heartbeat'})}\n\n".encode())
                
        except asyncio.CancelledError:
            pass
        finally:
            # Clean up connection
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            await response.write_eof()
        
        return response
    
    async def start_server(self, host: str = "localhost", port: int = 8000):
        """Start the HTTP server."""
        app = web.Application()
        
        # Tool endpoints
        app.router.add_post('/tool', self.handle_tool_call)
        app.router.add_get('/tools', self.handle_list_tools)
        
        # Resource endpoints
        app.router.add_get('/resources', self.handle_list_resources)
        app.router.add_get('/resources/{uri}', self.handle_read_resource)
        app.router.add_get('/search', self.handle_search_resources)
        app.router.add_get('/resources/popular', self.handle_popular_resources)
        app.router.add_get('/resources/recent', self.handle_recent_resources)
        
        # Prompt endpoints
        app.router.add_get('/prompts', self.handle_list_prompts)
        app.router.add_get('/prompts/{name}', self.handle_get_prompt)
        
        # SSE endpoint
        app.router.add_get('/sse', self.sse_handler)
        
        # Health check
        app.router.add_get('/health', lambda r: web.json_response({"status": "healthy"}))
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        
        print(f"🚀 HTTP MCP Server running on http://{host}:{port}")
        print(f"📋 Available endpoints:")
        print(f"  POST /tool - Call a tool")
        print(f"  GET  /tools - List all tools")
        print(f"  GET  /resources - List all resources")
        print(f"  GET  /resources/{{uri}} - Read a resource")
        print(f"  GET  /search - Search resources")
        print(f"  GET  /resources/popular - Get popular resources")
        print(f"  GET  /resources/recent - Get recent resources")
        print(f"  GET  /prompts - List all prompts")
        print(f"  GET  /prompts/{{name}} - Get a prompt")
        print(f"  GET  /sse - Server-Sent Events")
        print(f"  GET  /health - Health check")
        
        await site.start()
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour

async def main():
    """Main entry point for HTTP server."""
    server = HTTPMCPServer()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main()) 