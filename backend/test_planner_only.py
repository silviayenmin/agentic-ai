import asyncio
from agents.planner.agent import PlannerAgent

async def test_task_splitter():
    print("=" * 60)
    print("   Task Splitter (Planner) Interactive Test")
    print("   Type 'exit' or 'quit' to stop.")
    print("=" * 60)
    
    # Initialize agent
    planner = PlannerAgent()
    
    step = 1
    while True:
        try:
            # Get user input dynamically
            query = input(f"\n[STEP {step}] Enter your prompt: ").strip()
            
            # Exit condition
            if query.lower() in ['exit', 'quit']:
                print("\nExiting interactive test. Goodbye!")
                break
                
            if not query:
                continue
            
            print("\n[PLANNING] Generating response...")
            plan = await planner.plan(query)
            
            print("\n" + "=" * 20 + " AGENT OUTPUT " + "=" * 20)
            print(plan)
            print("=" * 60)
            
            step += 1
            
        except KeyboardInterrupt:
            print("\nExiting interactive test. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_task_splitter())

