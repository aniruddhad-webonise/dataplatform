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

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from core.sql_tools import SQLTools
from core.resource_manager import ResourceManager
from core.prompt_manager import PromptManager
from core.tool_loader import ToolLoader

# Load environment variables
load_dotenv()

class HTTPMCPServer:
    """HTTP wrapper for the MCP server with REST endpoints."""
    
    def __init__(self):
        self.sql_tools = SQLTools()
        self.resource_manager = ResourceManager()
        self.prompt_manager = PromptManager()
        self.tool_loader = ToolLoader()
        
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
                    arguments.get("db_connection", "sqlite:///./data/analytics.db")
                )
                
                # If storing as resource is requested, store the result
                if arguments.get("store_as_resource", True):
                    try:
                        result_data = json.loads(result)
                        if "data" in result_data:
                            uri = await self.resource_manager.store_table_resource(
                                result_data, 
                                arguments.get("sql_query")
                            )
                            if uri:
                                result_data["resource_uri"] = uri
                                result = json.dumps(result_data, indent=2)
                    except Exception as e:
                        print(f"Error storing resource: {e}")
                
                return web.json_response({
                    "status": "success",
                    "tool": tool_name,
                    "result": json.loads(result)
                })
            
            elif tool_name == "discover_schema":
                result = await self.sql_tools.discover_schema(
                    arguments.get("connection_string"),
                    arguments.get("include_sample_data", True),
                    arguments.get("max_sample_rows", 5)
                )
                
                # Store schema as resource
                try:
                    result_data = json.loads(result)
                    if "schema_uri" in result_data and "schema_data" in result_data:
                        uri = await self.resource_manager.store_schema_resource(
                            result_data["schema_data"],
                            result_data["schema_uri"]
                        )
                        if uri:
                            result_data["stored_uri"] = uri
                            result = json.dumps(result_data, indent=2)
                except Exception as e:
                    print(f"Error storing schema resource: {e}")
                
                return web.json_response({
                    "status": "success",
                    "tool": tool_name,
                    "result": json.loads(result)
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
    
    async def handle_read_resource(self, request):
        """Read a specific resource."""
        uri = request.match_info.get("uri")
        if not uri:
            return web.json_response({
                "status": "error",
                "error": "Resource URI is required"
            }, status=400)
        
        content = await self.resource_manager.read_resource(uri)
        return web.json_response({
            "status": "success",
            "uri": uri,
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