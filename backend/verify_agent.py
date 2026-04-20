import asyncio
import os
import sys

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = current_dir # Running from root
if root_dir not in sys.path:
    sys.path.append(root_dir)

from agents.chat.agent import ChatAgent

async def verify():
    print("Initializing Agent...")
    try:
        agent = ChatAgent()
        print(f"Agent '{agent.name}' initialized successfully.")
        print(f"Active Provider: {agent.global_config['active_provider']}")
        print(f"Model: {agent.global_config['providers'][agent.global_config['active_provider']]['model']}")
        
        # Test a simple non-blocking call
        print("\nTesting LLM connectivity (this may take a moment)...")
        # We use a very simple prompt to check if the tunnel and model are alive
        response = await agent.chat("Hi, just confirm you are online.")
        print(f"Response: {response}")
        print("\n✅ Verification Successful!")
        
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        if "404" in str(e) or "ConnectError" in str(e):
            print("Note: This often means the Ollama server or Tunnel is offline.")

if __name__ == "__main__":
    asyncio.run(verify())
