from langgraph.graph import START, StateGraph, END
from agents.agent import TripPlannerAgent, AgentState
from langgraph.types import Command

def main():
    agent = TripPlannerAgent()

    # 1️⃣ Gather input from the user
    user_input = {
        "number_of_days": int(input("Enter number of days for the trip: ")),
        "destination": input("Enter destination city: "),
        "departure": input("Enter departure city: "),
        "trip_start_date": input("Enter trip start date (YYYY-MM-DD): "),
        "number_of_people": int(input("Enter number of people: ")),
        # initialize empty fields for later
        "messages": [],
        "research": {},
        "weather": {},
        "flight": {},
        "hotel": {},
        "activities": {},
        "itinerary": {},
        "next": "",
        "current_reasoning": ""
    }

    initial_state: AgentState = user_input

    # 2️⃣ Build the workflow graph
    graph = StateGraph(AgentState)

    # Add actual implemented nodes
    graph.add_node("supervisor", agent.supervisor_node)
    graph.add_node("research_node", agent.research_node)
    graph.add_node("weather_node", agent.weather_node)
    graph.add_node("flight_node", agent.flight_node)
    graph.add_node("human_feedback_node", agent.human_feedback_node)

    # Stub the rest of the nodes to satisfy Router literals
    def stub_node(state: AgentState) -> Command:
        return Command(goto=END)  # just finish if ever called
    
    graph.add_node("hotel_node", stub_node)
    graph.add_node("activities_node", stub_node)
    graph.add_node("itirnerary_node", stub_node)
    # Edge from START to supervisor
    graph.add_edge(START, "supervisor")

    # Compile workflow
    app = graph.compile()

    # 3️⃣ Run the workflow from START with the initialized state
    final_state = app.invoke(initial_state)

    # 4️⃣ Print final state
    print("===================================")
    print("Final workflow state:")
    print(final_state)

if __name__ == "__main__":
    main()
