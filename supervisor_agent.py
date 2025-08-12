# supervisor_agent.py
from research_agent import run_research_agent

def supervisor_loop():
    print("Welcome to AI Travel Planner!")
    while True:
        user_input = input("You: ")
        agent_response = run_research_agent(user_input)
        print(f"Agent: {agent_response}")

        if agent_response.startswith("ALL_DETAILS_COLLECTED"):
            print("\n✅ Passing data to Supervisor for next steps...")
            break
