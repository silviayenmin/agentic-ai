import sys
import os
import json

# Add the current directory to sys.path to import from backend
sys.path.append(os.path.join(os.getcwd(), "backend"))

from main import agent_graph

def run_full_stack_test():
    print("🚀 Starting FULL STACK Multi-Agent Build (BE + FE + Tests)...")
    
    # NEW COMPREHENSIVE REQUIREMENT
    test_requirement = """
    Build a Reading List Application:
    1. Backend: Python FastAPI with endpoints to GET and POST books. 
    2. Storage: A JSON file named 'data.json' (initialized as an empty list).
    3. Frontend: A clean 'index.html' and 'style.css' that allows users to see the list and add books via the API.
    4. Testing: A 'test_api.py' file that uses 'pytest' or 'unittest' to verify the backend endpoints.
    5. Delivery: All files must be functional and work together.
    """
    
    initial_state = {
        "project_requirements": test_requirement,
        "provider": "ollama",
        "model": "llama3",
        "sprints": [],
        "tasks": [],
        "codebase": {},
        "qa_report": {},
        "status": "In Progress",
        "logs": ["System: Full-stack build started."],
        "iteration_count": 0
    }

    try:
        print("\n--- 🤖 Agents are working (this may take 2-5 minutes) ---\n")
        result = agent_graph.invoke(initial_state)

        print("\n--- 📜 System Logs ---")
        for log in result["logs"]:
            print(f"- {log}")

        print("\n--- ✅ Project Built Successfully! ---")
        print(f"Check the 'workspace/' folder for your project files.")
        print("\nTo run the project:")
        print("1. cd workspace")
        print("2. python -m uvicorn main:app --reload")
        print("3. Open index.html in your browser")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    run_full_stack_test()
