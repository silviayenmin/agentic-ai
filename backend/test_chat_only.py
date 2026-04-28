import asyncio
import sys
import os

# Ensure the backend directory is on sys.path so imports resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.chat.agent import ChatAgent

async def test_chat_agent():
    print("=" * 60)
    print("   Chat Agent Interactive Test")
    print("   Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    # Initialize agent
    agent = ChatAgent()
    print(f"\n[INFO] Agent initialized: {agent.name}")
    print(f"[INFO] Description: {agent.description}\n")

    step = 1
    while True:
        try:
            # Get user input dynamically
            query = input(f"\n[STEP {step}] You: ").strip()

            # Exit condition
            if query.lower() in ['exit', 'quit']:
                print("\nExiting interactive test. Goodbye!")
                break

            if not query:
                continue

            print("\n[THINKING] Generating response...")
            response = await agent.chat(query)

            print("\n" + "=" * 20 + " AGENT RESPONSE " + "=" * 20)
            print(response)
            print("=" * 60)

            step += 1

        except KeyboardInterrupt:
            print("\nExiting interactive test. Goodbye!")
            break
        except Exception as e:
            import traceback
            print(f"\n[ERROR] Test failed: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_agent())
