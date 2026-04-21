import asyncio
import json
import uuid
from datetime import datetime
from workflow.master_flow import build_master_workflow
from workflow.state import AgentState

# This mimics the state management logic found in main.py
def create_initial_state(requirements: str, user_id: str = "test_user") -> AgentState:
    return {
        "input": requirements,
        "chat_history": [],
        "analysis": "",
        "plan": "",
        "dependencies": "",
        "output": "",
        "evaluation_feedback": "",
        "next_step": "",
        "errors": []
    }

async def run_test_simulation():
    print("=" * 60)
    print("   Workflow Test Environment (System Integration Mode)")
    print("=" * 60)
    
    # Compile the graph
    app = build_master_workflow()
    
    # Simulated User Inputs
    test_scenarios = [
        "What is the weather like today?",
        "Create a simple FastAPI endpoint that greets the user."
    ]
    
    for query in test_scenarios:
        print(f"\n\n[TESTING] Input: {query}")
        state = create_initial_state(query)
        
        try:
            # Invoking the graph just like main.py does via websocket tasks
            result = app.invoke(state)
            
            print("\n" + "=" * 20 + " RESULTS " + "=" * 20)
            print(f"Workflow Decision: {result.get('next_step')}")
            print(f"Final Output: {result.get('output')}")
            if result.get('evaluation_feedback'):
                print(f"Quality Feedback: {result.get('evaluation_feedback')}")
            print("=" * 49)
            
        except Exception as e:
            print(f"\n[CRITICAL ERROR] Pipeline crash: {e}")

if __name__ == "__main__":
    asyncio.run(run_test_simulation())
