import subprocess
import json
import os
from typing import Dict, Any, List, Optional

class Tool:
    def __init__(self, name: str, func: callable, description: str):
        self.name = name
        self.func = func
        self.description = description

    def execute(self, **kwargs):
        return self.func(**kwargs)

class MCPTool:
    def __init__(self, name: str, command: str, args: List[str], env: Dict[str, str], auto_expand: bool = False):
        self.name = name
        self.command = command
        self.args = args
        self.env = {**os.environ, **env}
        self.auto_expand = auto_expand
        self._process = None

    def _ensure_process(self):
        if self._process is None or self._process.poll() is not None:
            self._process = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self.env,
                text=True,
                bufsize=1
            )

    def execute_sub_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        self._ensure_process()
        
        # Construct JSON-RPC request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            },
            "id": 1
        }
        
        try:
            # Send request
            json_req = json.dumps(request)
            self._process.stdin.write(json_req + "\n")
            self._process.stdin.flush()
            
            # Read response
            # This is a simplified reading mechanism. Real MCP needs robust framing.
            response_line = self._process.stdout.readline()
            if not response_line:
                return "Error: No response from MCP server"
                
            response = json.loads(response_line)
            
            if "error" in response:
                return f"MCP Error: {response['error']['message']}"
                
            if "result" in response:
                content = response["result"].get("content", [])
                text_content = [item["text"] for item in content if item["type"] == "text"]
                return "\n".join(text_content)
                
            return str(response)
            
        except Exception as e:
            return f"Error executing MCP tool: {str(e)}"

    def __del__(self):
        if self._process:
            self._process.terminate()
