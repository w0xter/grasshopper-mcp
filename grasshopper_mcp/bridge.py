import socket
import json
import os
import sys
import traceback
from typing import Dict, Any, Optional

# 使用 MCP 服務器
from mcp.server.fastmcp import FastMCP

# 設置 Grasshopper MCP 連接參數
GRASSHOPPER_HOST = "localhost"
GRASSHOPPER_PORT = 8080  # 默認端口，可以根據需要修改

# 創建 MCP 服務器
server = FastMCP("Grasshopper Bridge")

def send_to_grasshopper(command_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """向 Grasshopper MCP 發送命令"""
    if params is None:
        params = {}
    
    # 創建命令
    command = {
        "type": command_type,
        "parameters": params
    }
    
    try:
        print(f"Sending command to Grasshopper: {command_type} with params: {params}", file=sys.stderr)
        
        # 連接到 Grasshopper MCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((GRASSHOPPER_HOST, GRASSHOPPER_PORT))
        
        # 發送命令
        command_json = json.dumps(command)
        client.sendall((command_json + "\n").encode("utf-8"))
        print(f"Command sent: {command_json}", file=sys.stderr)
        
        # 接收響應
        response_data = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response_data += chunk
            if response_data.endswith(b"\n"):
                break
        
        # 處理可能的 BOM
        response_str = response_data.decode("utf-8-sig").strip()
        print(f"Response received: {response_str}", file=sys.stderr)
        
        # 解析 JSON 響應
        response = json.loads(response_str)
        client.close()
        return response
    except Exception as e:
        print(f"Error communicating with Grasshopper: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "success": False,
            "error": f"Error communicating with Grasshopper: {str(e)}"
        }

# 註冊 MCP 工具
@server.tool("add_component")
def add_component(component_type: str, x: float, y: float):
    """
    Add a component to the Grasshopper canvas
    
    Args:
        component_type: Component type (point, curve, circle, line, panel, slider)
        x: X coordinate on the canvas
        y: Y coordinate on the canvas
    
    Returns:
        Result of adding the component
    """
    params = {
        "type": component_type,
        "x": x,
        "y": y
    }
    
    return send_to_grasshopper("add_component", params)

@server.tool("clear_document")
def clear_document():
    """Clear the Grasshopper document"""
    return send_to_grasshopper("clear_document")

@server.tool("save_document")
def save_document(path: str):
    """
    Save the Grasshopper document
    
    Args:
        path: Save path
    
    Returns:
        Result of the save operation
    """
    params = {
        "path": path
    }
    
    return send_to_grasshopper("save_document", params)

@server.tool("load_document")
def load_document(path: str):
    """
    Load a Grasshopper document
    
    Args:
        path: Document path
    
    Returns:
        Result of the load operation
    """
    params = {
        "path": path
    }
    
    return send_to_grasshopper("load_document", params)

@server.tool("get_document_info")
def get_document_info():
    """Get information about the Grasshopper document"""
    return send_to_grasshopper("get_document_info")

@server.tool("connect_components")
def connect_components(source_id: str, target_id: str, source_param: str = None, target_param: str = None, source_param_index: int = None, target_param_index: int = None):
    """
    Connect two components in the Grasshopper canvas
    
    Args:
        source_id: ID of the source component (output)
        target_id: ID of the target component (input)
        source_param: Name of the source parameter (optional)
        target_param: Name of the target parameter (optional)
        source_param_index: Index of the source parameter (optional, used if source_param is not provided)
        target_param_index: Index of the target parameter (optional, used if target_param is not provided)
    
    Returns:
        Result of connecting the components
    """
    params = {
        "sourceId": source_id,
        "targetId": target_id
    }
    
    if source_param is not None:
        params["sourceParam"] = source_param
    elif source_param_index is not None:
        params["sourceParamIndex"] = source_param_index
        
    if target_param is not None:
        params["targetParam"] = target_param
    elif target_param_index is not None:
        params["targetParamIndex"] = target_param_index
    
    return send_to_grasshopper("connect_components", params)

@server.tool("create_pattern")
def create_pattern(description: str):
    """
    Create a pattern of components based on a high-level description
    
    Args:
        description: High-level description of what to create (e.g., '3D voronoi cube')
    
    Returns:
        Result of creating the pattern
    """
    params = {
        "description": description
    }
    
    return send_to_grasshopper("create_pattern", params)

@server.tool("get_available_patterns")
def get_available_patterns(query: str):
    """
    Get a list of available patterns that match a query
    
    Args:
        query: Query to search for patterns
    
    Returns:
        List of available patterns
    """
    params = {
        "query": query
    }
    
    return send_to_grasshopper("get_available_patterns", params)

# 註冊 MCP 資源
@server.resource("grasshopper://status")
def get_grasshopper_status():
    """Get Grasshopper status"""
    try:
        # 嘗試連接到 Grasshopper MCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((GRASSHOPPER_HOST, GRASSHOPPER_PORT))
        client.close()
        return {"status": "connected"}
    except:
        return {"status": "disconnected"}

@server.resource("grasshopper://component_guide")
def get_component_guide():
    """Get guide for Grasshopper components and connections"""
    return {
        "title": "Grasshopper Component Guide",
        "description": "Guide for creating and connecting Grasshopper components",
        "components": [
            {
                "name": "Point",
                "category": "Params",
                "description": "Creates a point at specific coordinates",
                "inputs": [
                    {"name": "X", "type": "Number"},
                    {"name": "Y", "type": "Number"},
                    {"name": "Z", "type": "Number"}
                ],
                "outputs": [
                    {"name": "Pt", "type": "Point"}
                ]
            },
            {
                "name": "Circle",
                "category": "Curve",
                "description": "Creates a circle",
                "inputs": [
                    {"name": "Plane", "type": "Plane", "description": "Base plane for the circle"},
                    {"name": "Radius", "type": "Number", "description": "Circle radius"}
                ],
                "outputs": [
                    {"name": "C", "type": "Circle"}
                ]
            },
            {
                "name": "XY Plane",
                "category": "Vector",
                "description": "Creates an XY plane at the world origin or at a specified point",
                "inputs": [
                    {"name": "Origin", "type": "Point", "description": "Origin point", "optional": True}
                ],
                "outputs": [
                    {"name": "Plane", "type": "Plane", "description": "XY plane"}
                ]
            }
        ],
        "connectionRules": [
            {
                "from": "Number",
                "to": "Circle.Radius",
                "description": "Connect a number to the radius input of a circle"
            },
            {
                "from": "Point",
                "to": "Circle.Plane",
                "description": "Connect a point to the plane input of a circle (not recommended, use XY Plane instead)"
            },
            {
                "from": "XY Plane",
                "to": "Circle.Plane",
                "description": "Connect an XY Plane to the plane input of a circle (recommended)"
            }
        ],
        "commonIssues": [
            "Using Point component instead of XY Plane for inputs that require planes",
            "Not specifying parameter names when connecting components",
            "Using incorrect GUIDs for Circle components"
        ],
        "tips": [
            "Always use XY Plane component for plane inputs",
            "Specify parameter names when connecting components",
            "For Circle components, make sure to use the correct GUID",
            "Test simple connections before creating complex geometry",
            "Avoid using components that require selection from Rhino"
        ]
    }

def main():
    """Main entry point for the Grasshopper MCP Bridge Server"""
    try:
        # 啟動 MCP 服務器
        print("Starting Grasshopper MCP Bridge Server...", file=sys.stderr)
        print("Please add this MCP server to Claude Desktop", file=sys.stderr)
        server.run()
    except Exception as e:
        print(f"Error starting MCP server: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
