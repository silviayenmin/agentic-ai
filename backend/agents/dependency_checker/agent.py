import os
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
 
 
class DependencyCheckerAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)
       
        # Correctly map tool names from config to tool functions
        tool_names = self.agent_config.get("tools", [])
        loaded_tools = self._load_tools(tool_names)
        self.tools = {name: tool for name, tool in zip(tool_names, loaded_tools)}
        print(f"[DependencyChecker] Tools Loaded: {list(self.tools.keys())}", flush=True)
 
    async def check_dependencies(self, query: str) -> str:
        """
        Analyzes dependencies using tools and saves the report to .agent_context/dependencies.md.
        """
        import sys
        import re
        import json
       
        history = self.memory.load_memory_variables({})["chat_history"]
       
        # Add a strict instruction to use tools first
        strict_query = (
            f"QUERY: {query}\n\n"
            "INSTRUCTION: \n"
            "1. Search the codebase FIRST using tools.\n"
            "2. If a search yields no results, try 2-3 alternative keywords or related terms.\n"
            "3. If after 3-5 different search patterns you still find NO evidence, STOP and provide a report stating it is missing. DO NOT keep guessing filenames indefinitely.\n"
            "4. Finally, provide a detailed report. Use: Action: tool_name({\"arg\": \"val\"})"
        )
       
        messages = [self.system_prompt] + history + [HumanMessage(content=strict_query)]
 
        final_response = ""
        last_tool_call = None
        # Tool calling loop (ReAct pattern)
        for i in range(30):  # Increased limit for deep analysis
            print(f"\n[DependencyChecker] Iteration {i+1}...", flush=True)
            response = await self.llm.ainvoke(messages)
            content = response.content
            final_response = content
            messages.append(response)
 
            # 1. Check for API-style tool calls
            tool_calls = getattr(response, "tool_calls", [])
           
            # 2. Check for Text-style tool calls (Action: tool_name({...}))
            action_match = re.search(r"Action:\s*(\w+)\s*\((.*)\)", content, re.DOTALL)
           
            # --- Loop Detection ---
            current_call = (tool_calls[0]["name"], tool_calls[0]["args"]) if tool_calls else (action_match.group(1), action_match.group(2)) if action_match else None
            if current_call and current_call == last_tool_call:
                print("[DependencyChecker] Loop detected (same tool/args), forcing summary.", flush=True)
                messages.append(HumanMessage(content="STRICT INSTRUCTION: You are repeating yourself. STOP calling tools immediately. Based on the tool results you ALREADY have, provide the final structured report now. DO NOT include any more 'Action:' or tool calls."))
                response = await self.llm.ainvoke(messages)
                # Clean up the response to remove any lingering Action lines if the AI was stubborn
                final_response = re.sub(r"Action:\s*\w+\(.*\)", "", response.content, flags=re.DOTALL).strip()
                break
            last_tool_call = current_call
 
            if not tool_calls and not action_match:
                # If the last response was too short or looks like a polite brush-off,
                # force one more call to get a real report.
                is_polite_brush_off = any(phrase in content.lower() for phrase in ["thank you", "feel free to ask", "assistance with this project", "i couldn't find", "as an ai"])
                if len(content) < 300 or is_polite_brush_off:
                    print("[DependencyChecker] Response looks like a brush-off or incomplete, forcing a detailed report...", flush=True)
                    messages.append(HumanMessage(content="You have not provided a complete technical report. Based on the tools available and your findings, provide a FINAL structured report now. Mention specific files found or explicitly list what was searched and found missing. DO NOT be polite, just be technical."))
                    response = await self.llm.ainvoke(messages)
                    final_response = response.content
                else:
                    final_response = content
                print("[DependencyChecker] Finishing.", flush=True)
                break
 
            # Process API Tool Calls
            for tool_call in tool_calls:
                tool_name = tool_call["name"].split(".")[-1]
                tool_args = tool_call["args"]
                print(f"[DependencyChecker] API Tool Call: {tool_name} with args: {tool_args}", flush=True)
                await self._run_tool(tool_name, tool_args, tool_call["id"], messages)
 
            # Process Text Tool Calls
            if action_match:
                tool_name = action_match.group(1)
                tool_args_str = action_match.group(2).strip()
                try:
                    # Clean up JSON if LLM added single quotes or other mess
                    tool_args_str = tool_args_str.replace("'", "\"")
                    tool_args = json.loads(tool_args_str)
                    print(f"[DependencyChecker] Text Tool Call: {tool_name} with args: {tool_args}", flush=True)
                    await self._run_tool(tool_name, tool_args, f"text_{i}", messages)
                except Exception as e:
                    messages.append(HumanMessage(content=f"Error parsing tool arguments: {e}"))
 
        self.memory.save_context({"input": query}, {"output": final_response})
       
        # Save dependency report
        dep_path = ".agent_context/dependencies.md"
        os.makedirs(os.path.dirname(dep_path), exist_ok=True)
        with open(dep_path, "w", encoding="utf-8") as f:
            f.write(final_response)
           
        return final_response
 
    async def _run_tool(self, name, args, call_id, messages):
        if name in self.tools:
            try:
                # Use ainvoke to handle both sync and async tools correctly
                result = await self.tools[name].ainvoke(args)
                messages.append(ToolMessage(tool_call_id=call_id, content=str(result)))
                print(f"[DependencyChecker] Tool Result: Success", flush=True)
            except Exception as e:
                messages.append(ToolMessage(tool_call_id=call_id, content=f"Error: {e}"))
                print(f"[DependencyChecker] Tool Result: Error: {e}", flush=True)
        else:
            messages.append(ToolMessage(tool_call_id=call_id, content=f"Tool {name} not found."))
            print(f"[DependencyChecker] Tool Result: Not Found", flush=True)
 
 