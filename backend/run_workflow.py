import asyncio
from workflow.master_flow import build_master_workflow

async def run_system():
    print("=" * 60)
    print("   Agentic Orchestrator System Started")
    print("=" * 60)
    
    # Initialize the compiled graph
    app = build_master_workflow()
    
    while True:
        user_input = input("\nYou (Query): ")
        if user_input.lower() in ["exit", "quit"]:
            break
            
        print(f"\n[System] Routing your request...")
        
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
            
            print("\n" + "=" * 20 + " RESULTS " + "=" * 20)
            print(f"Decision: {result.get('next_step')}")
            print(f"Output: {result.get('output')}")
            if result.get('evaluation_feedback'):
                print(f"Evaluator Feedback: {result.get('evaluation_feedback')}")
            print("=" * 49)
            
        except Exception as e:
            print(f"\n[System Error] An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(run_system())
