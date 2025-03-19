# Grasshopper MCP Bridge

Grasshopper MCP Bridge is a bridging server that connects Grasshopper and Claude Desktop using the Model Context Protocol (MCP) standard.

## Features

- Connects Grasshopper and Claude Desktop through the MCP protocol
- Provides intuitive tool functions for creating and connecting Grasshopper components
- Supports high-level intent recognition, automatically creating complex component patterns from simple descriptions
- Includes a component knowledge base that understands parameters and connection rules for common components
- Provides component guidance resources to help Claude Desktop correctly connect components

## System Architecture

The system consists of the following parts:

1. **Grasshopper MCP Component (GH_MCP.gha)**: A plugin installed in Grasshopper that provides a TCP server to receive commands
2. **Python MCP Bridge Server**: A bridge server that connects Claude Desktop and the Grasshopper MCP component
3. **Component Knowledge Base**: JSON files containing component information, patterns, and intents

## Installation Instructions

### Prerequisites

- Rhino 7 or higher
- Grasshopper
- Python 3.8 or higher
- Claude Desktop

### Installation Steps

1. **Install the Grasshopper MCP Component**

   **Method 1: Download the pre-compiled GH_MCP.gha file (Recommended)**
   
   Download the [GH_MCP.gha](https://github.com/alfredatnycu/grasshopper-mcp/raw/master/releases/GH_MCP.gha) file directly from the GitHub repository and copy it to the Grasshopper components folder:
   ```
   %APPDATA%\Grasshopper\Libraries\
   ```

   **Method 2: Build from source**
   
   If you prefer to build from source, clone the repository and build the C# project using Visual Studio.

2. **Install the Python MCP Bridge Server**

   **Method 1: Install from PyPI (Recommended)**
   
   The simplest method is to install directly from PyPI using pip:
   ```
   pip install grasshopper-mcp
   ```
   
   **Method 2: Install from GitHub**
   
   You can also install the latest version from GitHub:
   ```
   pip install git+https://github.com/alfredatnycu/grasshopper-mcp.git
   ```
   
   **Method 3: Install from Source Code**
   
   If you need to modify the code or develop new features, you can clone the repository and install:
   ```
   git clone https://github.com/alfredatnycu/grasshopper-mcp.git
   cd grasshopper-mcp
   pip install -e .
   ```

   **Install a Specific Version**
   
   If you need to install a specific version, you can use:
   ```
   pip install grasshopper-mcp==0.1.0
   ```
   Or install from a specific GitHub tag:
   ```
   pip install git+https://github.com/alfredatnycu/grasshopper-mcp.git@v0.1.0
   ```

## Usage

1. **Start Rhino and Grasshopper**

2. **Start the Python MCP Bridge Server**

   In a terminal, run:
   ```
   grasshopper-mcp
   ```

3. **Add the MCP Server to Claude Desktop**

   In Claude Desktop's settings, add the following MCP server configuration:
   ```json
   {
     "mcpServers": {
       "grasshopper": {
         "command": "grasshopper-mcp",
         "args": []
       }
     }
   }
   ```

4. **Use Claude Desktop to Interact with Grasshopper**

   Now you can use Claude Desktop to send commands to Grasshopper, such as:
   - "Create a 3D Voronoi in Grasshopper"
   - "Add a circle component"
   - "Connect the point and circle components"

## Available Tools

- `add_component`: Adds a component to the Grasshopper canvas
- `connect_components`: Connects two components
- `create_pattern`: Creates a component pattern based on a high-level description
- `get_available_patterns`: Gets a list of available patterns
- `clear_document`: Clears the Grasshopper document
- `save_document`: Saves the Grasshopper document
- `load_document`: Loads a Grasshopper document
- `get_document_info`: Gets document information

## Developer Guide

### Project Structure

```
grasshopper-mcp/
├── grasshopper_mcp/          # Python package
│   ├── __init__.py
│   └── bridge.py             # MCP bridge server
├── GH_MCP/                   # Grasshopper component source code
│   ├── GH_MCP/
│   │   ├── Commands/         # Command handlers
│   │   ├── Models/           # Data models
│   │   ├── Resources/        # Resource files
│   │   └── Utils/            # Utility classes
│   └── GH_MCP.sln            # Visual Studio solution
├── releases/                 # Pre-compiled binaries
│   └── GH_MCP.gha           # Compiled Grasshopper component
├── setup.py                  # Python package configuration
└── README.md                 # This file
```

### Adding New Features

1. **Add a New Grasshopper Command**

   Create a new command handler in the `GH_MCP/Commands/` directory and register it in `GrasshopperCommandRegistry.cs`.

2. **Add a New MCP Tool**

   In `grasshopper_mcp/bridge.py`, use the `@server.tool` decorator to add a new tool function.

3. **Extend the Component Knowledge Base**

   Add new components, patterns, or intents to the `ComponentKnowledgeBase.json` file.

## Contribution Guide

Contributions are welcome! Before submitting code, please ensure:

1. Code follows the project's coding style
2. Appropriate tests are added
3. Documentation is updated

## License

MIT License
