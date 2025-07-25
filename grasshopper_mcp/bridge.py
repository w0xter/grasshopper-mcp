import socket
import json
import os
import sys
import traceback
from typing import Dict, Any, Optional, List
import uuid

# 使用 MCP 服務器
from mcp.server.fastmcp import FastMCP

# 設置 Grasshopper MCP 連接參數
GRASSHOPPER_HOST = "localhost"
GRASSHOPPER_PORT = 8080  # 默認端口，可以根據需要修改

# 創建 MCP 服務器
server = FastMCP("Grasshopper Bridge")

# Path to the shared component knowledge base JSON
KNOWLEDGE_BASE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "GH_MCP", "GH_MCP", "Resources", "ComponentKnowledgeBase.json")
)

_knowledge_base_cache: Optional[Dict[str, Any]] = None

def load_knowledge_base() -> Dict[str, Any]:
    """Load the shared component knowledge base JSON."""
    global _knowledge_base_cache
    if _knowledge_base_cache is None:
        try:
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                _knowledge_base_cache = json.load(f)
        except Exception as e:
            print(f"Error loading knowledge base: {e}", file=sys.stderr)
            _knowledge_base_cache = {}
    return _knowledge_base_cache

def send_to_grasshopper(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Send a JSON-RPC request to the Grasshopper MCP server."""
    if params is None:
        params = {}

    request_id = str(uuid.uuid4())
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params,
    }

    client = None
    try:
        print(
            f"Sending request to Grasshopper: {method} with params: {params}",
            file=sys.stderr,
        )

        # Connect to Grasshopper MCP with a longer timeout
        client = socket.create_connection(
            (GRASSHOPPER_HOST, GRASSHOPPER_PORT), timeout=30
        )
        client.settimeout(30)

        # Send the JSON-RPC request
        request_json = json.dumps(request)
        client.sendall((request_json + "\n").encode("utf-8"))
        print(f"Request sent: {request_json}", file=sys.stderr)

        # Receive the response
        response_data = b""
        try:
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    if not response_data:
                        raise ConnectionError("Connection closed before response received")
                    break
                response_data += chunk
                if response_data.endswith(b"\n"):
                    break
        except socket.timeout:
            return {
                "success": False,
                "error": "Timed out waiting for response from Grasshopper",
            }

        if not response_data.endswith(b"\n"):
            return {
                "success": False,
                "error": "Incomplete response from Grasshopper",
            }

        response_str = response_data.decode("utf-8-sig").strip()
        print(f"Response received: {response_str}", file=sys.stderr)

        response = json.loads(response_str)

        # Unwrap JSON-RPC envelope if present
        if isinstance(response, dict) and response.get("jsonrpc") == "2.0":
            if "result" in response:
                return response["result"]
            elif "error" in response:
                return {
                    "success": False,
                    "error": response.get("error"),
                }
        return response

    except socket.timeout:
        return {
            "success": False,
            "error": "Timed out communicating with Grasshopper",
        }
    except Exception as e:
        print(f"Error communicating with Grasshopper: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "success": False,
            "error": f"Error communicating with Grasshopper: {str(e)}"
        }
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass

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
    # 處理常見的組件名稱混淆問題
    component_mapping = {
        # Number Slider 的各種可能輸入方式
        "number slider": "Number Slider",
        "numeric slider": "Number Slider",
        "num slider": "Number Slider",
        "slider": "Number Slider",  # 當只提到 slider 且上下文是數值時，預設為 Number Slider
        
        # 其他組件的標準化名稱
        "md slider": "MD Slider",
        "multidimensional slider": "MD Slider",
        "multi-dimensional slider": "MD Slider",
        "graph mapper": "Graph Mapper",
        
        # 數學運算組件
        "add": "Addition",
        "addition": "Addition",
        "plus": "Addition",
        "sum": "Addition",
        "subtract": "Subtraction",
        "subtraction": "Subtraction",
        "minus": "Subtraction",
        "difference": "Subtraction",
        "multiply": "Multiplication",
        "multiplication": "Multiplication",
        "times": "Multiplication",
        "product": "Multiplication",
        "divide": "Division",
        "division": "Division",
        
        # 輸出組件
        "panel": "Panel",
        "text panel": "Panel",
        "output panel": "Panel",
        "display": "Panel"
    }
    
    # 檢查並修正組件類型
    normalized_type = component_type.lower()
    if normalized_type in component_mapping:
        component_type = component_mapping[normalized_type]
        print(f"Component type normalized from '{normalized_type}' to '{component_mapping[normalized_type]}'", file=sys.stderr)
    
    params = {
        "type": component_type,
        "x": x,
        "y": y
    }

    return send_to_grasshopper("add_component", params)

@server.tool("delete_component")
def delete_component(component_id: str):
    """Delete a component from the Grasshopper canvas"""
    params = {
        "id": component_id
    }

    return send_to_grasshopper("delete_component", params)

@server.tool("move_component")
def move_component(component_id: str, x: float, y: float):
    """Move an existing component to a new canvas location"""
    params = {
        "id": component_id,
        "x": x,
        "y": y
    }

    return send_to_grasshopper("move_component", params)

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

    response = send_to_grasshopper("save_document", params)

    if not response.get("success", False):
        error_msg = response.get("error") or response.get("message", "Unknown error")
        raise RuntimeError(f"Failed to save document: {error_msg}")

    return response.get("result") or response.get("data") or response

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

    response = send_to_grasshopper("load_document", params)

    if not response.get("success", False):
        error_msg = response.get("error") or response.get("message", "Unknown error")
        raise RuntimeError(f"Failed to load document: {error_msg}")

    return response.get("result") or response.get("data") or response

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
    # 獲取目標組件的信息，檢查是否已有連接
    target_info = send_to_grasshopper("get_component_info", {"componentId": target_id})
    
    # 檢查組件類型，如果是需要多個輸入的組件（如 Addition, Subtraction 等），智能分配輸入
    if target_info and "result" in target_info and "type" in target_info["result"]:
        component_type = target_info["result"]["type"]
        
        # 獲取現有連接
        connections = send_to_grasshopper("get_connections")
        existing_connections = []
        
        if connections and "result" in connections:
            for conn in connections["result"]:
                if conn.get("targetId") == target_id:
                    existing_connections.append(conn)
        
        # 對於特定需要多個輸入的組件，自動選擇正確的輸入端口
        if component_type in ["Addition", "Subtraction", "Multiplication", "Division", "Math"]:
            # 如果沒有指定目標參數，且已有連接到第一個輸入，則自動連接到第二個輸入
            if target_param is None and target_param_index is None:
                # 檢查第一個輸入是否已被佔用
                first_input_occupied = False
                for conn in existing_connections:
                    if conn.get("targetParam") == "A" or conn.get("targetParamIndex") == 0:
                        first_input_occupied = True
                        break
                
                # 如果第一個輸入已被佔用，則連接到第二個輸入
                if first_input_occupied:
                    target_param = "B"  # 第二個輸入通常命名為 B
                else:
                    target_param = "A"  # 否則連接到第一個輸入
    
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

@server.tool("get_component_info")
def get_component_info(component_id: str):
    """
    Get detailed information about a specific component
    
    Args:
        component_id: ID of the component to get information about
    
    Returns:
        Detailed information about the component, including inputs, outputs, and current values
    """
    params = {
        "componentId": component_id
    }
    
    result = send_to_grasshopper("get_component_info", params)
    
    # 增強返回結果，添加更多參數信息
    if result and "result" in result:
        component_data = result["result"]
        
        # 獲取組件類型
        if "type" in component_data:
            component_type = component_data["type"]
            
            # 查詢組件庫，獲取該類型組件的詳細參數信息
            component_library = get_component_library()
            if "components" in component_library:
                for lib_component in component_library["components"]:
                    if lib_component.get("name") == component_type or lib_component.get("fullName") == component_type:
                        # 將組件庫中的參數信息合併到返回結果中
                        if "settings" in lib_component:
                            component_data["availableSettings"] = lib_component["settings"]
                        if "inputs" in lib_component:
                            component_data["inputDetails"] = lib_component["inputs"]
                        if "outputs" in lib_component:
                            component_data["outputDetails"] = lib_component["outputs"]
                        if "usage_examples" in lib_component:
                            component_data["usageExamples"] = lib_component["usage_examples"]
                        if "common_issues" in lib_component:
                            component_data["commonIssues"] = lib_component["common_issues"]
                        break
            
            # 特殊處理某些組件類型
            if component_type == "Number Slider":
                # 嘗試從組件數據中獲取當前滑桿的實際設置
                if "currentSettings" not in component_data:
                    component_data["currentSettings"] = {
                        "min": component_data.get("min", 0),
                        "max": component_data.get("max", 10),
                        "value": component_data.get("value", 5),
                        "rounding": component_data.get("rounding", 0.1),
                        "type": component_data.get("type", "float")
                    }
            
            # 添加組件的連接信息
            connections = send_to_grasshopper("get_connections")
            if connections and "result" in connections:
                # 查找與該組件相關的所有連接
                related_connections = []
                for conn in connections["result"]:
                    if conn.get("sourceId") == component_id or conn.get("targetId") == component_id:
                        related_connections.append(conn)
                
                if related_connections:
                    component_data["connections"] = related_connections
    
    return result

@server.tool("set_component_value")
def set_component_value(component_id: str, value: str):
    """
    Set the value of a Grasshopper component.

    This can update panel text, slider values or the first input of a
    component by forwarding the request to the Grasshopper MCP server.

    Args:
        component_id: ID of the component to update
        value: New value as a string

    Returns:
        Result returned by Grasshopper after applying the value
    """
    params = {
        "id": component_id,
        "value": value
    }

    return send_to_grasshopper("set_component_value", params)

@server.tool("get_all_components")
def get_all_components():
    """
    Get a list of all components in the current document
    
    Returns:
        List of all components in the document with their IDs, types, and positions
    """
    result = send_to_grasshopper("get_all_components")
    
    # 增強返回結果，為每個組件添加更多參數信息
    if result and "result" in result:
        components = result["result"]
        component_library = get_component_library()
        
        # 獲取所有連接信息
        connections = send_to_grasshopper("get_connections")
        connections_data = connections.get("result", []) if connections else []
        
        # 為每個組件添加詳細信息
        for component in components:
            if "id" in component and "type" in component:
                component_id = component["id"]
                component_type = component["type"]
                
                # 添加組件的詳細參數信息
                if "components" in component_library:
                    for lib_component in component_library["components"]:
                        if lib_component.get("name") == component_type or lib_component.get("fullName") == component_type:
                            # 將組件庫中的參數信息合併到組件數據中
                            if "settings" in lib_component:
                                component["availableSettings"] = lib_component["settings"]
                            if "inputs" in lib_component:
                                component["inputDetails"] = lib_component["inputs"]
                            if "outputs" in lib_component:
                                component["outputDetails"] = lib_component["outputs"]
                            break
                
                # 添加組件的連接信息
                related_connections = []
                for conn in connections_data:
                    if conn.get("sourceId") == component_id or conn.get("targetId") == component_id:
                        related_connections.append(conn)
                
                if related_connections:
                    component["connections"] = related_connections
                
                # 特殊處理某些組件類型
                if component_type == "Number Slider":
                    # 嘗試獲取滑桿的當前設置
                    component_info = send_to_grasshopper("get_component_info", {"componentId": component_id})
                    if component_info and "result" in component_info:
                        info_data = component_info["result"]
                        component["currentSettings"] = {
                            "min": info_data.get("min", 0),
                            "max": info_data.get("max", 10),
                            "value": info_data.get("value", 5),
                            "rounding": info_data.get("rounding", 0.1)
                        }
    
    return result

@server.tool("get_connections")
def get_connections():
    """
    Get a list of all connections between components in the current document
    
    Returns:
        List of all connections between components
    """
    return send_to_grasshopper("get_connections")

@server.tool("search_components")
def search_components(query: str):
    """
    Search for components by name or category
    
    Args:
        query: Search query
    
    Returns:
        List of components matching the search query
    """
    params = {
        "query": query
    }
    
    return send_to_grasshopper("search_components", params)

@server.tool("get_component_parameters")
def get_component_parameters(component_type: str):
    """
    Get a list of parameters for a specific component type
    
    Args:
        component_type: Type of component to get parameters for
    
    Returns:
        List of input and output parameters for the component type
    """
    params = {
        "componentType": component_type
    }
    
    return send_to_grasshopper("get_component_parameters", params)

@server.tool("validate_connection")
def validate_connection(source_id: str, target_id: str, source_param: str = None, target_param: str = None):
    """
    Validate if a connection between two components is possible
    
    Args:
        source_id: ID of the source component (output)
        target_id: ID of the target component (input)
        source_param: Name of the source parameter (optional)
        target_param: Name of the target parameter (optional)
    
    Returns:
        Whether the connection is valid and any potential issues
    """
    params = {
        "sourceId": source_id,
        "targetId": target_id
    }
    
    if source_param is not None:
        params["sourceParam"] = source_param
        
    if target_param is not None:
        params["targetParam"] = target_param

    return send_to_grasshopper("validate_connection", params)

@server.tool("execute_preview")
def execute_preview():
    """Force a new solution preview in Grasshopper"""
    return send_to_grasshopper("execute_preview")

@server.tool("execute_script")
def execute_script(script: str):
    """Execute a Rhino command script"""
    params = {"script": script}
    return send_to_grasshopper("execute_script", params)

@server.tool("create_macro")
def create_macro(name: str, macro: str):
    """Store a named Rhino macro"""
    params = {"name": name, "macro": macro}
    return send_to_grasshopper("create_macro", params)

@server.tool("run_macro")
def run_macro(name: str = None, macro: str = None):
    """Run a stored or inline Rhino macro"""
    params = {}
    if name is not None:
        params["name"] = name
    if macro is not None:
        params["macro"] = macro
    return send_to_grasshopper("run_macro", params)

@server.tool("snapshot")
def snapshot(name: str = None):
    """Create a snapshot of the current document"""
    params = {}
    if name is not None:
        params["name"] = name
    return send_to_grasshopper("snapshot", params)

@server.tool("revert_snapshot")
def revert_snapshot(name: str):
    """Revert to a previously created snapshot"""
    params = {"name": name}
    return send_to_grasshopper("revert_snapshot", params)

@server.tool("get_geometry")
def get_geometry(component_id: str):
    """Get preview geometry data for a component"""
    params = {"id": component_id}
    return send_to_grasshopper("get_geometry", params)

@server.tool("run_gh_python")
def run_gh_python(script: str):
    """Execute Python script inside Rhino"""
    params = {"script": script}
    return send_to_grasshopper("run_gh_python", params)

# 註冊 MCP 資源
@server.resource("grasshopper://status")
def get_grasshopper_status():
    """Get Grasshopper status"""
    try:
        # 獲取文檔信息
        doc_info = send_to_grasshopper("get_document_info")
        
        # 獲取所有組件（使用增強版的 get_all_components）
        components_result = get_all_components()
        components = components_result.get("result", []) if components_result else []
        
        # 獲取所有連接
        connections = send_to_grasshopper("get_connections")
        
        # 添加常用組件的提示信息
        component_hints = load_knowledge_base().get("componentHints", {})
        
        # 為每個組件添加當前參數值的摘要
        component_summaries = []
        for component in components:
            summary = {
                "id": component.get("id", ""),
                "type": component.get("type", ""),
                "position": {
                    "x": component.get("x", 0),
                    "y": component.get("y", 0)
                }
            }
            
            # 添加組件特定的參數信息
            if "currentSettings" in component:
                summary["settings"] = component["currentSettings"]
            elif component.get("type") == "Number Slider":
                # 嘗試從組件信息中提取滑桿設置
                summary["settings"] = {
                    "min": component.get("min", 0),
                    "max": component.get("max", 10),
                    "value": component.get("value", 5),
                    "rounding": component.get("rounding", 0.1)
                }
            
            # 添加連接信息摘要
            if "connections" in component:
                conn_summary = []
                for conn in component["connections"]:
                    if conn.get("sourceId") == component.get("id"):
                        conn_summary.append({
                            "type": "output",
                            "to": conn.get("targetId", ""),
                            "sourceParam": conn.get("sourceParam", ""),
                            "targetParam": conn.get("targetParam", "")
                        })
                    else:
                        conn_summary.append({
                            "type": "input",
                            "from": conn.get("sourceId", ""),
                            "sourceParam": conn.get("sourceParam", ""),
                            "targetParam": conn.get("targetParam", "")
                        })
                
                if conn_summary:
                    summary["connections"] = conn_summary
            
            component_summaries.append(summary)
        
        return {
            "status": "Connected to Grasshopper",
            "document": doc_info.get("result", {}),
            "components": component_summaries,
            "connections": connections.get("result", []),
            "component_hints": component_hints,
            "recommendations": [
                "When needing a simple numeric input control, ALWAYS use 'Number Slider', not MD Slider",
                "For vector inputs (like 3D points), use 'MD Slider' or 'Construct Point' with multiple Number Sliders",
                "Use 'Panel' to display outputs and debug values",
                "When connecting multiple sliders to Addition, first slider goes to input A, second to input B"
            ],
            "canvas_summary": f"Current canvas has {len(component_summaries)} components and {len(connections.get('result', []))} connections"
        }
    except Exception as e:
        print(f"Error getting Grasshopper status: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "status": f"Error: {str(e)}",
            "document": {},
            "components": [],
            "connections": []
        }

@server.resource("grasshopper://component_guide")
def get_component_guide():
    """Get guide for Grasshopper components and connections"""
    return load_knowledge_base().get("componentGuide", {})

@server.resource("grasshopper://component_library")
def get_component_library():
    """Get a comprehensive library of Grasshopper components"""
    return load_knowledge_base().get("componentLibrary", {})

@server.resource("grasshopper://component_hints")
def get_component_hints():
    """Get common hints for Grasshopper components"""
    return load_knowledge_base().get("componentHints", {})

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
