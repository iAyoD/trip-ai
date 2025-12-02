import os
from typing import List, Dict, Any, Optional, Callable
import json
from openai import OpenAI
from hello_agents.tools import MCPTool, Tool
import re
import asyncio
import concurrent.futures
from fastmcp import Client

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
        self.tools: Dict[str, Tool] = {}

    def _run_sync(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        else:
            return asyncio.run(coro)

    def add_tool(self, mcp_tool: MCPTool):
        """
        添加 MCP 工具，并绑定执行逻辑
        """
        print(f"正在加载 MCP 工具集: {mcp_tool.name} ...")
        
        # 1. 获取工具列表
        try:
            tool_list = self._run_sync(mcp_tool.list_tools())
        except Exception as e:
            print(f"获取工具列表失败: {e}")
            return

        # 2. 注册工具
        for tool_item in tool_list:
            # 构建 Tool 对象
            args_desc = json.dumps(tool_item.inputSchema) if hasattr(tool_item, 'inputSchema') else "{}"
            
            new_tool = Tool(
                name=tool_item.name,
                description=tool_item.description,
                args=args_desc,
                config=mcp_tool.config
            )

            # 存入字典
            self.tools[tool_item.name] = new_tool
            print(f"  - 已加载工具: {tool_item.name}")

    def get_tools_description(self) -> str:
        """
        获取所有可用工具的格式化描述字符串

        Returns:
            工具描述字符串，用于构建提示词
        """
        descriptions = []

        # Tool对象描述
        for tool in self.tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}, Args: {tool.args}")

        return "\n".join(descriptions) if descriptions else "暂无可用工具"

    def _get_enhanced_prompt(self, system_prompt: str) -> str:
        """构建增强的系统提示词，包含工具信息"""
        base_prompt = self.system_prompt or "你是一个有用的AI助手。"
        
        # 获取工具描述
        tools_description = self.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            print(f"未发现可用工具，使用基础提示词")
            return base_prompt
        
        tools_section = "\n\n## 可用工具\n"
        tools_section += "你可以使用以下工具来帮助回答问题：\n"
        tools_section += tools_description + "\n"

        tools_section += "\n## 工具调用格式\n"
        tools_section += "当需要使用工具时，请使用以下格式：\n"
        tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n\n"

        tools_section += "### 参数格式说明\n"
        tools_section += "1. **多个参数**：使用 `key=value` 格式，用逗号分隔\n"
        tools_section += "   示例：`[TOOL_CALL:calculator_multiply:a=12,b=8]`\n"
        tools_section += "2. **单个参数**：直接使用 `key=value`\n"
        tools_section += "   示例：`[TOOL_CALL:search:query=Python编程]`\n\n"

        tools_section += "### 重要提示\n"
        tools_section += "- 参数名必须与工具定义的参数名完全匹配\n"
        tools_section += "- 数字参数直接写数字，不需要引号：`a=12` 而不是 `a=\"12\"`\n"
        tools_section += "- 工具调用结果会自动插入到对话中，然后你可以基于结果继续回答\n"

        return base_prompt + tools_section

    async def run(self, user_input: str) -> str:
        # 将工具描述添加到系统提示中
        self.system_prompt = self._get_enhanced_prompt(self.system_prompt)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # 1. 获取 LLM 的回复
        response = self.llm.chat(messages)

        print(f"{self.name} 回复: {response}")
        
        # 2. 检查是否包含工具调用
        # Format: [TOOL_CALL:tool_name:arg1=val1,arg2=val2]
        tool_calls = re.findall(r'\[TOOL_CALL:([^:]+):([^\]]+)\]', response)
        
        if tool_calls:
            for tool_name, args_str in tool_calls:
                args = {}
                if args_str:
                    for pair in args_str.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            args[k.strip()] = v.strip()
                
                # 执行工具
                tool_result = f"错误: 未找到工具 {tool_name}"
                
                if tool_name in self.tools:
                    print(f"{self.name} 执行工具 {tool_name}，参数: {args}")
                    tool_result = await self.tools[tool_name].run(args)
                
                # 3. 将工具结果反馈给 LLM
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": f"工具输出: {tool_result}\n请继续。"})
                final_response = self.llm.chat(messages)
                return final_response
        else:
            print(f"{self.name} 未发现工具调用，直接返回: {response}")
            return response
