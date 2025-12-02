import subprocess
import json
import os
from typing import Dict, Any, List, Optional
import logging
from fastmcp import Client
import asyncio

class Tool:
    def __init__(self, name: str, description: str, args: str, config: Dict[str, Any]):
        self.name = name
        self.description = description
        self.args = args
        self.config = config

    async def run(self, args: Dict[str, Any]) -> str:
        try:
            client = Client(self.config)
            async with client:
                result = await client.call_tool(self.name, args)
            return result
            
        except Exception as e:
            return f"执行 MCP 工具时出错: {str(e)}"

class MCPTool:
    def __init__(self, name: str, command: str, args: List[str], env: Dict[str, str], auto_expand: bool = False):
        self.name = name
        self.command = command
        self.args = args
        self.env = env

        self._construct_config()

    def _construct_config(self):
        self.config = {
            "mcpServers": {
                self.name: {
                "command": self.command,
                "args": self.args,
                "env": self.env
                }
            }
        }

    async def list_tools(self):
        client = Client(self.config)
        async with client:
            tools = await client.list_tools()
        return tools