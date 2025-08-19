"""
MCP (Model Context Protocol) 设置
配置MCP客户端和服务器连接
"""

MCP_CONFIG = {
    "server": {
        "name": "playwright",
        "command": "npx",
        "args": ["-y", "@executeautomation/playwright-mcp-server"],
        "timeout": 30,
        "max_retries": 3
    },
    "client": {
        "timeout": 60,
        "max_concurrent_requests": 5
    },
    "logging": {
        "level": "INFO",
        "file": "logs/mcp.log"
    }
}

# Claude Desktop 配置模板
CLAUDE_DESKTOP_CONFIG = {
    "mcpServers": {
        "playwright": {
            "command": "npx",
            "args": ["-y", "@executeautomation/playwright-mcp-server"],
            "env": {
                "PLAYWRIGHT_HEADLESS": "true",
                "PLAYWRIGHT_TIMEOUT": "30000"
            }
        }
    }
}

# MCP工具功能配置
MCP_TOOLS = {
    "browser": {
        "navigate": "playwright_navigate",
        "screenshot": "playwright_screenshot", 
        "click": "playwright_click",
        "type": "playwright_type",
        "wait": "playwright_wait_for_selector",
        "extract_text": "playwright_extract_text",
        "extract_table": "playwright_extract_table"
    },
    "data_extraction": {
        "enabled": True,
        "formats": ["json", "csv", "html"],
        "validation": True
    }
}