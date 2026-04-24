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

            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return {"category": "UNKNOWN", "reason": "Failed to parse LLM response as JSON"}
