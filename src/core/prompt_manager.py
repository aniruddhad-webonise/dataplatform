"""
Prompt Manager for the MCP server.
Handles interactive workflow templates and prompt discovery.
"""

from typing import List, Dict, Any, Optional

class PromptManager:
    """Manages interactive prompts for the MCP server."""
    
    def __init__(self):
        self.prompts = self._initialize_prompts()
    
    def _initialize_prompts(self) -> Dict[str, str]:
        """Initialize the available prompts."""
        return {
            "explore_table": """# Explore Table Data

Use this prompt to explore and analyze table data.

**Parameters:**
- `table_uri`: URI of the table resource to explore
- `limit`: Number of rows to preview (default: 5)

**Example:**
```
/explore_table resource://tables/abc123?limit=10
```

**Workflow:**
1. Read the table resource
2. Show preview of data
3. Provide basic statistics
4. Suggest potential analysis directions

**Tools to use:**
- `read_resource` to get table data
- `generate_sql` for additional queries if needed
""",

            "visualize_growth": """# Visualize Growth Trends

Use this prompt to create visualizations for growth and trend analysis.

**Parameters:**
- `table_uri`: URI of the table resource to visualize
- `trend_type`: Type of trend to analyze (growth, decline, seasonal, etc.)

**Example:**
```
/visualize_growth resource://tables/abc123 trend
```

**Workflow:**
1. Analyze the table data for time-based columns
2. Identify growth patterns
3. Generate appropriate visualization
4. Store chart as resource
5. Provide insights about the trends

**Tools to use:**
- `read_resource` to get table data
- `create_viz` to generate charts
- `store_chart_resource` to save visualization
""",

            "predict": """# Predictive Analysis

Use this prompt to perform predictive analysis on table data.

**Parameters:**
- `table_uri`: URI of the table resource to analyze
- `target_column`: Column to predict
- `prediction_type`: Type of prediction (regression, classification, etc.)

**Example:**
```
/predict resource://tables/abc123 sales_amount regression
```

**Workflow:**
1. Analyze the table structure and data
2. Identify features for prediction
3. Run predictive model
4. Store results as ML resource
5. Provide prediction insights and accuracy metrics

**Tools to use:**
- `read_resource` to get table data
- `predictive_model` to run ML analysis
- `store_ml_resource` to save results
""",

            "auto_insights": """# Automatic Insights Generation

Use this prompt to automatically generate comprehensive insights from table data.

**Parameters:**
- `table_uri`: URI of the table resource to analyze

**Example:**
```
/auto_insights resource://tables/abc123
```

**Workflow:**
1. Perform comprehensive data analysis
2. Generate summary statistics
3. Identify top correlations
4. Create relevant visualizations
5. Provide actionable insights
6. Store all results as resources

**Tools to use:**
- `read_resource` to get table data
- `generate_sql` for additional analysis queries
- `create_viz` for multiple chart types
- `predictive_model` for basic predictions
- Store all results as resources
""",

            "explain_chart": """# Chart Explanation

Use this prompt to get detailed explanations of charts and visualizations.

**Parameters:**
- `chart_uri`: URI of the chart resource to explain

**Example:**
```
/explain_chart resource://charts/def456
```

**Workflow:**
1. Read the chart resource
2. Analyze the visualization data
3. Provide detailed explanation of what the chart shows
4. Highlight key insights and patterns
5. Suggest potential actions based on the data

**Tools to use:**
- `read_resource` to get chart data
- AI analysis for interpretation
""",

            "sql_sandbox": """# Interactive SQL Sandbox

Use this prompt to create an interactive SQL development environment.

**Parameters:**
- `initial_query`: Starting SQL query (optional)
- `db_connection`: Database connection string

**Example:**
```
/sql_sandbox "SELECT * FROM users LIMIT 5"
```

**Workflow:**
1. Start with initial query (if provided)
2. Execute and show results
3. Allow iterative modifications
4. Validate each query
5. Store successful results as resources
6. Provide suggestions for improvements

**Tools to use:**
- `generate_sql` for query generation
- `validate_sql` for safety checks
- `execute_sql` for running queries
- `store_table_resource` for saving results
""",

            "data_quality": """# Data Quality Assessment

Use this prompt to assess the quality of table data.

**Parameters:**
- `table_uri`: URI of the table resource to assess

**Example:**
```
/data_quality resource://tables/abc123
```

**Workflow:**
1. Analyze data completeness
2. Check for missing values
3. Identify outliers and anomalies
4. Assess data consistency
5. Generate quality report
6. Suggest data cleaning steps

**Tools to use:**
- `read_resource` to get table data
- `generate_sql` for quality analysis queries
- `create_viz` for quality visualizations
""",

            "export_data": """# Data Export

Use this prompt to export table data in various formats.

**Parameters:**
- `table_uri`: URI of the table resource to export
- `format`: Export format (csv, json, excel)

**Example:**
```
/export_data resource://tables/abc123 csv
```

**Workflow:**
1. Read the table resource
2. Convert to requested format
3. Generate download link or file
4. Provide format-specific metadata

**Tools to use:**
- `read_resource` to get table data
- `export_csv` for CSV export
- `export_json` for JSON export
"""
        }
    
    async def list_prompts(self) -> List[str]:
        """List all available prompts."""
        return list(self.prompts.keys())
    
    async def get_prompt(self, name: str) -> str:
        """Get a specific prompt template."""
        return self.prompts.get(name, f"Prompt '{name}' not found.")
    
    async def add_prompt(self, name: str, template: str) -> bool:
        """Add a new prompt template."""
        try:
            self.prompts[name] = template
            return True
        except Exception:
            return False
    
    async def remove_prompt(self, name: str) -> bool:
        """Remove a prompt template."""
        try:
            if name in self.prompts:
                del self.prompts[name]
                return True
            return False
        except Exception:
            return False
    
    async def search_prompts(self, query: str) -> List[str]:
        """Search prompts by content."""
        matching_prompts = []
        query_lower = query.lower()
        
        for name, template in self.prompts.items():
            if query_lower in name.lower() or query_lower in template.lower():
                matching_prompts.append(name)
        
        return matching_prompts
    
    async def get_prompt_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata about a specific prompt."""
        if name not in self.prompts:
            return {"error": f"Prompt '{name}' not found."}
        
        template = self.prompts[name]
        
        # Extract basic metadata
        metadata = {
            "name": name,
            "description": self._extract_description(template),
            "parameters": self._extract_parameters(template),
            "examples": self._extract_examples(template),
            "tools": self._extract_tools(template),
            "workflow_steps": self._extract_workflow(template)
        }
        
        return metadata
    
    def _extract_description(self, template: str) -> str:
        """Extract description from prompt template."""
        lines = template.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "No description available"
    
    def _extract_parameters(self, template: str) -> List[str]:
        """Extract parameters from prompt template."""
        parameters = []
        in_params_section = False
        
        for line in template.split('\n'):
            if '**Parameters:**' in line:
                in_params_section = True
                continue
            elif in_params_section and line.startswith('**'):
                break
            elif in_params_section and line.strip().startswith('- `'):
                param = line.strip()[3:].split('`')[0]
                parameters.append(param)
        
        return parameters
    
    def _extract_examples(self, template: str) -> List[str]:
        """Extract examples from prompt template."""
        examples = []
        in_examples_section = False
        
        for line in template.split('\n'):
            if '**Example:**' in line:
                in_examples_section = True
                continue
            elif in_examples_section and line.startswith('**'):
                break
            elif in_examples_section and line.strip().startswith('```'):
                continue
            elif in_examples_section and line.strip():
                examples.append(line.strip())
        
        return examples
    
    def _extract_tools(self, template: str) -> List[str]:
        """Extract tools from prompt template."""
        tools = []
        in_tools_section = False
        
        for line in template.split('\n'):
            if '**Tools to use:**' in line:
                in_tools_section = True
                continue
            elif in_tools_section and line.startswith('**'):
                break
            elif in_tools_section and line.strip().startswith('- `'):
                tool = line.strip()[3:].split('`')[0]
                tools.append(tool)
        
        return tools
    
    def _extract_workflow(self, template: str) -> List[str]:
        """Extract workflow steps from prompt template."""
        workflow = []
        in_workflow_section = False
        
        for line in template.split('\n'):
            if '**Workflow:**' in line:
                in_workflow_section = True
                continue
            elif in_workflow_section and line.startswith('**'):
                break
            elif in_workflow_section and line.strip().startswith('1. '):
                step = line.strip()[3:]
                workflow.append(step)
            elif in_workflow_section and line.strip().startswith('2. '):
                step = line.strip()[3:]
                workflow.append(step)
            elif in_workflow_section and line.strip().startswith('3. '):
                step = line.strip()[3:]
                workflow.append(step)
            elif in_workflow_section and line.strip().startswith('4. '):
                step = line.strip()[3:]
                workflow.append(step)
            elif in_workflow_section and line.strip().startswith('5. '):
                step = line.strip()[3:]
                workflow.append(step)
            elif in_workflow_section and line.strip().startswith('6. '):
                step = line.strip()[3:]
                workflow.append(step)
        
        return workflow 