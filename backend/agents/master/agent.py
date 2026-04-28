import os
import json
from agents.base_agent import BaseAgent
from langchain_core.messages import HumanMessage


class MasterAgent(BaseAgent):
    def __init__(self):
        # Pass the current directory to the base class
        current_dir = os.path.dirname(os.path.abspath(__file__))
        super().__init__(agent_dir=current_dir)

    async def route_query(self, user_input: str) -> dict:
        """
        Routes the user query to the appropriate category.
        """
        history = self.memory.load_memory_variables({})["chat_history"]
        
        # Enforce structured output via prompt instructions if not using bind_tools
        routing_instruction = (
            "Analyze the query and respond in ONLY valid JSON format: "
            "{\"category\": \"CHAT\" | \"CODING\", \"reason\": \"string\"}"
        )
        
        messages = [self.system_prompt] + history + [HumanMessage(content=f"{routing_instruction}\n\nQuery: {user_input}")]

        response = await self.invoke_llm(messages)
        self.memory.save_context({"input": user_input}, {"output": response.content})
        
        try:
            # Clean response in case the LLM adds markdown triple backticks or conversational filler
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # If it's still not valid JSON, try to find the first '{' and last '}'
            if not (content.startswith("{") and content.endswith("}")):
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    content = content[start:end+1]

            decision = json.loads(content)
            
            # Ensure category is upper case and valid
            cat = str(decision.get("category", "CHAT")).upper()
            if cat not in ["CHAT", "CODING"]:
                cat = "CHAT"
            decision["category"] = cat
            return decision

        except (json.JSONDecodeError, ValueError, Exception):
            # HEURISTIC FALLBACK: If parsing fails, check for technical keywords
            technical_keywords = [
                "create", "modify", "debug", "react", "component", "redux", 
                "file", "folder", "npm", "install", "code", "function", "javascript"
            ]
            lower_input = user_input.lower()
            if any(kw in lower_input for kw in technical_keywords):
                return {
                    "category": "CODING", 
                    "reason": "Heuristic fallback: Technical keywords detected in query."
                }
            
            return {
                "category": "CHAT", 
                "reason": "Defaulting to CHAT due to parsing failure and no clear technical keywords."
            }
