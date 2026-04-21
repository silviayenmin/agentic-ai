import asyncio
import os
import sys

# Ensure the root directory is in the path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from workflow.master_flow import build_master_workflow

async def main():
    print("=" * 60)
    print("   Workflow Test Environment (Testing System)")
    print("=" * 60)
    
    # Initialize the compiled graph
    try:
        app = build_master_workflow()
        print("[System] Workflow graph compiled successfully.")
    except Exception as e:
        print(f"[Error] Failed to compile workflow: {e}")
        return
    
    while True:
        user_input = input("\nTest Query: ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        print(f"\n[Testing] Routing: {user_input}")
        
        # Initialize state with the user input
        initial_state = {
            "input": user_input,
            "chat_history": [],
            "analysis": "",
            "plan": "",
            "dependencies": "",
            "output": "",
            "evaluation_feedback": "",
            "next_step": "",
            "errors": []
        }
        
        try:
            # Run the graph
            result = app.invoke(initial_state)
            
            print("\n" + "=" * 20 + " TEST RESULTS " + "=" * 20)
            print(f"Decision: {result.get('next_step')}")
            print(f"Output: {result.get('output')}")
            if result.get('evaluation_feedback'):
                print(f"Evaluator Feedback: {result.get('evaluation_feedback')}")
            print("=" * 54)
            
        except Exception as e:
            print(f"\n[Test Error] An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
