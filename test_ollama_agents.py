import sys
import os
import json
import asyncio

# Add the current directory to sys.path to import from backend
sys.path.append(os.path.join(os.getcwd(), "backend"))

from main import agent_graph

async def test_run():
    print("🚀 Starting Async Multi-Agent Test with Ollama (qwen2.5-coder:14b)...")
    
    test_requirement = "Build a simple Python CLI tool that manages a reading list."
    
    initial_state = {
        "project_requirements": test_requirement,
        "provider": "ollama",
        "model": "qwen2.5-coder:14b",
        "sprints": [],
        "tasks": [],
        "codebase": {},
        "qa_report": {},
        "current_agent": "BA",
        "agent_statuses": {"BA": "idle", "PM": "idle", "Dev": "idle", "QA": "idle", "Monitor": "idle"},
        "logs": [],
        "iteration_count": 0
    }

    try:
        print("\n--- Running Agents (Async) ---\n")
        # Use ainvoke for async nodes
        result = await agent_graph.ainvoke(initial_state)

        print("\n--- 📋 Sprints ---")
        print(json.dumps(result["sprints"], indent=2))

        print("\n--- 🛠️ Task Backlog ---")
        print(json.dumps(result["tasks"], indent=2))

        print("\n--- 📜 System Logs ---")
        for log in result["logs"]:
            print(f"- {log}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_run())
