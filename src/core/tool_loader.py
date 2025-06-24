"""
Tool Loader for the MCP server.
Loads tool definitions from individual XML files and converts them to MCP Tool objects.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any
from mcp.types import Tool

class ToolLoader:
    """Loads tool definitions from XML files."""
    
    def __init__(self, tools_dir: str = "src/tools"):
        self.tools_dir = Path(tools_dir)
        self.tools_cache: Dict[str, Tool] = {}
    
    def load_all_tools(self) -> List[Tool]:
        """Load all tools from XML files in the tools directory."""
        tools = []
        
        if not self.tools_dir.exists():
            print(f"Warning: Tools directory {self.tools_dir} does not exist")
            return tools
        
        # Find all XML files in the tools directory
        xml_files = list(self.tools_dir.glob("*.xml"))
        
        for xml_file in xml_files:
            try:
                tool = self._load_tool_from_xml(xml_file)
                if tool:
                    tools.append(tool)
                    self.tools_cache[tool.name] = tool
                    print(f"Loaded tool: {tool.name}")
            except Exception as e:
                print(f"Error loading tool from {xml_file}: {e}")
        
        return tools
    
    def _load_tool_from_xml(self, xml_file: Path) -> Tool:
        """Load a single tool from an XML file."""
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Extract tool name
        tool_name = root.get("name")
        if not tool_name:
            raise ValueError(f"Tool name not found in {xml_file}")
        
        # Extract description
        description_elem = root.find("description")
        description = description_elem.text if description_elem is not None else ""
        
        # Build input schema
        input_schema = self._build_input_schema(root)
        
        return Tool(
            name=tool_name,
            description=description,
            inputSchema=input_schema
        )
    
    def _build_input_schema(self, root: ET.Element) -> Dict[str, Any]:
        """Build the input schema from XML parameters."""
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        parameters_elem = root.find("parameters")
        if parameters_elem is None:
            return schema
        
        for param_elem in parameters_elem.findall("parameter"):
            param_name = param_elem.get("name")
            param_type = param_elem.get("type")
            param_required = param_elem.get("required", "false").lower() == "true"
            param_default = param_elem.get("default")
            
            # Get parameter description
            desc_elem = param_elem.find("description")
            param_description = desc_elem.text if desc_elem is not None else ""
            
            # Build parameter definition
            param_def = {
                "type": self._convert_xml_type_to_json(param_type),
                "description": param_description
            }
            
            # Add default value if specified
            if param_default is not None:
                param_def["default"] = self._parse_default_value(param_default, param_type)
            
            # Handle array types
            if param_type == "array":
                param_def["items"] = {"type": "string"}  # Default to string array
            
            # Handle object types
            if param_type == "object":
                param_def["additionalProperties"] = True
            
            schema["properties"][param_name] = param_def
            
            if param_required:
                schema["required"].append(param_name)
        
        return schema
    
    def _convert_xml_type_to_json(self, xml_type: str) -> str:
        """Convert XML type to JSON schema type."""
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "number": "number",
            "boolean": "boolean",
            "array": "array",
            "object": "object"
        }
        return type_mapping.get(xml_type, "string")
    
    def _parse_default_value(self, default_value: str, param_type: str) -> Any:
        """Parse default value based on parameter type."""
        if param_type == "boolean":
            return default_value.lower() == "true"
        elif param_type == "integer":
            return int(default_value)
        elif param_type == "number":
            return float(default_value)
        elif param_type == "array":
            # Simple array parsing - could be enhanced
            if default_value.startswith("[") and default_value.endswith("]"):
                return []
            return []
        elif param_type == "object":
            # Simple object parsing - could be enhanced
            if default_value.startswith("{") and default_value.endswith("}"):
                return {}
            return {}
        else:
            return default_value
    
    def get_tool(self, name: str) -> Tool:
        """Get a specific tool by name."""
        return self.tools_cache.get(name)
    
    def get_tool_examples(self, name: str) -> List[Dict[str, Any]]:
        """Get examples for a specific tool."""
        xml_file = self.tools_dir / f"{name}.xml"
        if not xml_file.exists():
            return []
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            examples = []
            examples_elem = root.find("examples")
            if examples_elem is None:
                return examples
            
            for example_elem in examples_elem.findall("example"):
                input_elem = example_elem.find("input")
                output_elem = example_elem.find("output")
                
                if input_elem is None or output_elem is None:
                    continue
                
                # Parse input parameters
                input_params = {}
                for param in input_elem:
                    input_params[param.tag] = param.text
                
                # Parse output parameters
                output_params = {}
                for param in output_elem:
                    output_params[param.tag] = param.text
                
                examples.append({
                    "input": input_params,
                    "output": output_params
                })
            
            return examples
            
        except Exception as e:
            print(f"Error loading examples for tool {name}: {e}")
            return []
    
    def list_available_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self.tools_cache.keys())
    
    def reload_tools(self) -> List[Tool]:
        """Reload all tools from XML files."""
        self.tools_cache.clear()
        return self.load_all_tools() 