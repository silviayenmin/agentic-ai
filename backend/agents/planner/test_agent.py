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
from agents.planner.agent import PlannerAgent

async def run_test():
    # Set the working directory to root so the agent can find 'config.json'
    os.chdir(root_dir)
    
    # Initialize the agent
    agent = PlannerAgent()

    print("=" * 50)
    print(f"Agent '{agent.name}' is ready!")
    print(f"Using Provider: {agent.global_config['active_provider']}")
    print("Type 'exit' or 'quit' to stop.")
    print("=" * 50)

    while True:
        user_input = input("\nYou (Analysis to Plan): ")

        if user_input.lower() in ["exit", "quit"]:
            break

        try:
            # The agent uses the bound tools and buffer memory
            response = await agent.plan(user_input)
            print(f"\nPlan:\n{response}")
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
