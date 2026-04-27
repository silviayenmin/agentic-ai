import asyncio
import os
import sys

# Setup root path so it can find 'agents' and 'tools'
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from agents.analyzer.agent import AnalyzerAgent

async def run_batch_test():
    # Set working directory to root
    os.chdir(root_dir)
    
    agent = AnalyzerAgent()
    print(f"Starting Batch Test for agent: {agent.name}\n")

    scenarios = {
        "todo_app": "build a basic todo application with python",
        "auth_function": "write a javascript function for user authentication",
        "weather_api": "weather api integration",
        "banking_dashboard": "requirement for a banking dashboard with real-time balance",
        "user_profile": "user profile system with image upload and edit features"
    }

    # Create a directory for results
    results_dir = os.path.join(root_dir, "test_results")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    for key, query in scenarios.items():
        print(f"Analysing Scenario: {key}...")
        try:
            # Analyze
            response = await agent.analyze(query)
            
            # Save to specific file
            output_file = os.path.join(results_dir, f"{key}_analysis.md")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# Analysis for: {query}\n\n")
                f.write(response)
            
            print(f"  Done -> {output_file}")
        except Exception as e:
            print(f"  Error on {key}: {e}")

    print(f"\nBatch test complete! Check the results in: {results_dir}")

if __name__ == "__main__":
    asyncio.run(run_batch_test())
