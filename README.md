# Advanced MCP SQL Analytics Server

A Model Context Protocol (MCP) server that provides comprehensive SQL analytics capabilities with tools, resources, and prompts for multi-step data workflows.

## 🚀 Development Sprint Plan

### Day 1: Foundation ✅
- [x] Set up MCP server with official SDK
- [x] Core SQL tools (`generate_sql`, `validate_sql`, `execute_sql`)
- [x] Basic resource management for table snapshots
- [x] Simple test interface
- [x] **XML-based tool definitions** (modular architecture)
- [x] **Tool loader with examples and metadata**

### Day 2: Resources & State
- [ ] Full resource URI system
- [ ] Table/chart/ML result storage
- [ ] Resource metadata and lifecycle management
- [ ] Resource cleanup and expiration

### Day 3: Prompts & Workflows
- [ ] Interactive prompt system
- [ ] Multi-step workflow orchestration
- [ ] User-friendly prompt discovery
- [ ] Composable prompts

### Day 4: Advanced Features
- [ ] Visualization tools
- [ ] ML prediction capabilities
- [ ] Export and sharing features
- [ ] Production deployment

## Features

- **Tools**: Generate, validate, and execute SQL queries
- **Resources**: Persistent storage of tables, charts, and ML results
- **Prompts**: Interactive workflows for data exploration
- **Multi-step Analytics**: From SQL generation to visualization to ML predictions
- **Resource URIs**: Reference stored artifacts across conversations
- **XML Tool Definitions**: Modular, maintainable tool architecture

## Architecture

### XML-Based Tool System
Tools are defined in individual XML files in `src/tools/`:

```
src/tools/
├── generate_sql.xml      # Natural language to SQL conversion
├── validate_sql.xml      # SQL validation and security checks
├── execute_sql.xml       # Database execution with resource storage
├── create_viz.xml        # Chart generation (Day 3)
└── predictive_model.xml  # ML predictions (Day 4)
```

Each XML file contains:
- **Parameters**: Input schema with types and descriptions
- **Returns**: Output structure definition
- **Examples**: Real-world usage examples
- **Metadata**: Tool capabilities and constraints

### Benefits of XML Architecture
1. **Modularity**: Add new tools without touching code
2. **Rich Metadata**: Comprehensive examples and descriptions
3. **Easy Maintenance**: Update tool definitions independently
4. **Better Discovery**: MCP clients understand tool capabilities
5. **Consistency**: Standardized tool definition format

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp env.example .env
# Edit .env with your OpenAI API key
```

3. Run tests:
```bash
python test_server.py
```

4. Run the server:
```bash
python src/main.py
```

## Tool Examples

### Generate SQL
```xml
<tool name="generate_sql">
    <parameters>
        <parameter name="nl_query" type="string" required="true">
            <description>Natural language description of the desired SQL query</description>
        </parameter>
        <parameter name="db_type" type="string" required="false" default="postgresql">
            <description>Database type (postgresql, mysql, sqlite, oracle)</description>
        </parameter>
    </parameters>
</tool>
```

### Execute SQL with Resource Storage
```xml
<tool name="execute_sql">
    <parameters>
        <parameter name="sql_query" type="string" required="true">
            <description>SQL query to execute</description>
        </parameter>
        <parameter name="store_as_resource" type="boolean" required="false" default="true">
            <description>Whether to store results as a resource for later reference</description>
        </parameter>
    </parameters>
</tool>
```

## Resource System

Resources are stored with URIs for persistent reference:
- `resource://tables/abc123` - Table snapshots
- `resource://charts/def456` - Generated visualizations
- `resource://ml/ghi789` - ML model results

