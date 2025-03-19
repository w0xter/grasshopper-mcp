# Grasshopper MCP Bridge

Grasshopper MCP Bridge 是一個連接 Grasshopper 和 Claude Desktop 的橋接服務器，使用 Model Context Protocol (MCP) 標準協議。

## 功能特點

- 通過 MCP 協議連接 Grasshopper 和 Claude Desktop
- 提供直觀的工具函數，用於創建和連接 Grasshopper 組件
- 支持高層次意圖識別，可以從簡單描述自動創建複雜的組件模式
- 包含組件知識庫，了解常用組件的參數和連接規則
- 提供組件指南資源，幫助 Claude Desktop 正確連接組件

## 系統架構

該系統由以下部分組成：

1. **Grasshopper MCP 組件 (GH_MCP.gha)**：安裝在 Grasshopper 中的插件，提供 TCP 服務器接收命令
2. **Python MCP 橋接服務器**：連接 Claude Desktop 和 Grasshopper MCP 組件的橋接服務器
3. **組件知識庫**：包含組件信息、模式和意圖的 JSON 文件

## 安裝說明

### 前提條件

- Rhino 7 或更高版本
- Grasshopper
- Python 3.8 或更高版本
- Claude Desktop

### 安裝步驟

1. **安裝 Grasshopper MCP 組件**

   將 `GH_MCP.gha` 文件複製到 Grasshopper 組件文件夾：
   ```
   %APPDATA%\Grasshopper\Libraries\
   ```

2. **安裝 Python MCP 橋接服務器**

   使用 pip 安裝：
   ```
   pip install grasshopper-mcp
   ```

   或從源代碼安裝：
   ```
   git clone https://github.com/alfredatnycu/grasshopper-mcp.git
   cd grasshopper-mcp
   pip install -e .
   ```

## 使用方法

1. **啟動 Rhino 和 Grasshopper**

2. **啟動 MCP 橋接服務器**

   在命令行中運行：
   ```
   grasshopper-mcp
   ```

3. **在 Claude Desktop 中添加 MCP 服務器**

   在 Claude Desktop 的設置中添加以下 MCP 服務器配置：
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

4. **使用 Claude Desktop 與 Grasshopper 交互**

   現在您可以使用 Claude Desktop 向 Grasshopper 發送命令，例如：
   - "在 Grasshopper 中創建一個 3D Voronoi"
   - "添加一個圓形組件"
   - "連接點和圓形組件"

## 可用工具

- `add_component`：添加組件到 Grasshopper 畫布
- `connect_components`：連接兩個組件
- `create_pattern`：根據高層次描述創建組件模式
- `get_available_patterns`：獲取可用的模式列表
- `clear_document`：清空 Grasshopper 文檔
- `save_document`：保存 Grasshopper 文檔
- `load_document`：加載 Grasshopper 文檔
- `get_document_info`：獲取文檔信息

## 開發者指南

### 項目結構

```
grasshopper-mcp/
├── grasshopper_mcp/          # Python 包
│   ├── __init__.py
│   └── bridge.py             # MCP 橋接服務器
├── GH_MCP/                   # Grasshopper 組件源代碼
│   ├── GH_MCP/
│   │   ├── Commands/         # 命令處理器
│   │   ├── Models/           # 數據模型
│   │   ├── Resources/        # 資源文件
│   │   └── Utils/            # 工具類
│   └── GH_MCP.sln            # Visual Studio 解決方案
├── setup.py                  # Python 包配置
└── README.md                 # 說明文檔
```

### 添加新功能

1. **添加新的 Grasshopper 命令**

   在 `GH_MCP/Commands/` 目錄中創建新的命令處理器，並在 `GrasshopperCommandRegistry.cs` 中註冊。

2. **添加新的 MCP 工具**

   在 `grasshopper_mcp/bridge.py` 中使用 `@server.tool` 裝飾器添加新的工具函數。

3. **擴展組件知識庫**

   在 `ComponentKnowledgeBase.json` 中添加新的組件、模式或意圖。

## 貢獻指南

歡迎提交 Pull Request 或 Issue 來改進這個項目。在提交代碼前，請確保：

1. 代碼符合項目的編碼風格
2. 添加了適當的測試
3. 更新了文檔

## 許可證

MIT 許可證
