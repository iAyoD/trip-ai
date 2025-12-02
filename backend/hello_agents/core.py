import os
from typing import List, Dict, Any, Optional, Callable
import json
from openai import OpenAI

class HelloAgentsLLM:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.model = os.getenv("OPENAI_MODEL_NAME", "gpt-3.5-turbo")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content

class SimpleAgent:
    def __init__(self, name: str, llm: HelloAgentsLLM, system_prompt: str):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.tools: Dict[str, Any] = {}

    def add_tool(self, tool: Any):
        if hasattr(tool, 'auto_expand') and tool.auto_expand:
            # For MCP tools that expand into multiple tools
            # This is a simplification; in a real scenario we'd query the MCP server
            # But for now we'll just store the main tool and let it handle dispatch
            self.tools[tool.name] = tool
        else:
            self.tools[tool.name] = tool

    def run(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # 1. Get initial response from LLM
        response = self.llm.chat(messages)
        
        # 2. Check for tool calls
        # Format: [TOOL_CALL:tool_name:arg1=val1,arg2=val2]
        if "[TOOL_CALL:" in response:
            start = response.find("[TOOL_CALL:")
            end = response.find("]", start)
            if end != -1:
                tool_call_str = response[start+11:end]
                parts = tool_call_str.split(":")
                tool_name = parts[0]
                args_str = parts[1] if len(parts) > 1 else ""
                
                # Parse args
                args = {}
                if args_str:
                    for pair in args_str.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            args[k.strip()] = v.strip()
                
                # Execute tool
                # In our simplified MCP implementation, we might need to find which tool object handles this
                # For now, let's assume we look through registered tools
                tool_result = f"Error: Tool {tool_name} not found"
                
                # Check if it's a direct tool or part of an MCP tool
                if tool_name in self.tools:
                    tool_result = self.tools[tool_name].execute(**args)
                else:
                    # Check MCP tools
                    for tool in self.tools.values():
                        if hasattr(tool, 'execute_sub_tool'):
                            try:
                                tool_result = tool.execute_sub_tool(tool_name, args)
                                break
                            except:
                                continue
                
                # 3. Feed result back to LLM
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"Tool Output: {tool_result}\nPlease continue."})
                final_response = self.llm.chat(messages)
                return final_response
                
        return response
