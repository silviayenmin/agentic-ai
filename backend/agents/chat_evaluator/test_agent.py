import asyncio
import os
import sys

# This section allows the script to find the 'agents' and 'Tools' packages 
# even when run from inside this sub-folder.
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import using the full path now that root is in sys.path
from agents.chat_evaluator.agent import ChatEvaluatorAgent

async def run_test():
    # Set the working directory to root so the agent can find 'config.json'
    os.chdir(root_dir)
    
    # Initialize the agent
    agent = ChatEvaluatorAgent()

    print("=" * 50)
    print(f"Agent '{agent.name}' is ready!")
    print(f"Using Provider: {agent.global_config['active_provider']}")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 50)

    while True:
        request = input("\nOriginal User Request: ")
        if request.lower() in ["exit", "quit"]: break
        
        proposed = input("Proposed Response to Evaluate: ")
        if proposed.lower() in ["exit", "quit"]: break

        try:
            # The agent uses the bound tools and buffer memory
            response = await agent.evaluate(request, proposed)
            print(f"\nEvaluation Output:\n{response}")
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
