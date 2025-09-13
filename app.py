import streamlit as st
from langgraph.graph import StateGraph, START, END
from agents.agent import TripPlannerAgent, AgentState
from langgraph.types import Command


def build_graph(agent: TripPlannerAgent):
    graph = StateGraph(AgentState)

    # Add actual implemented nodes
    graph.add_node("supervisor", agent.supervisor_node)
    graph.add_node("research_node", agent.research_node)
    graph.add_node("weather_node", agent.weather_node)
    graph.add_node("flight_node", agent.flight_node)
    graph.add_node("hotel_node", agent.hotel_node)
    graph.add_node("activities_node", agent.activities_node)
    graph.add_node("human_feedback_node", agent.human_feedback_node)
    graph.add_node("itinerary_node", agent.itinerary_node)

    # Edge from START → supervisor
    graph.add_edge(START, "supervisor")

    return graph.compile()


def run_trip_planner(user_input: dict):
    agent = TripPlannerAgent()
    app = build_graph(agent)
    final_state = app.invoke(user_input)
    return final_state


def main():
    st.set_page_config(page_title="AI Trip Planner", page_icon="✈️", layout="wide")

    st.title("✈️ AI Trip Planner")
    st.markdown("Plan your trip with AI: flights, hotels, activities, and full itinerary.")

    with st.form("trip_form"):
        col1, col2 = st.columns(2)

        with col1:
            number_of_days = st.number_input("Number of Days", min_value=1, step=1)
            destination = st.text_input("Destination City", placeholder="e.g. Bali")
            departure = st.text_input("Departure City", placeholder="e.g. Goa")

        with col2:
            trip_start_date = st.date_input("Trip Start Date")
            number_of_people = st.number_input("Number of People", min_value=1, step=1)

        submitted = st.form_submit_button("Plan My Trip 🚀")

    if submitted:
        # Build initial state
        user_input = {
            "number_of_days": number_of_days,
            "destination": destination,
            "departure": departure,
            "trip_start_date": str(trip_start_date),
            "number_of_people": number_of_people,
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

        with st.spinner("Generating your personalized trip plan..."):
            final_state = run_trip_planner(user_input)

        st.success("✅ Trip Plan Generated!")

        # Display results
        st.subheader("🗓️ Itinerary")
        st.write(final_state.get("itinerary", "No itinerary available"))

        st.subheader("✈️ Flights")
        st.write(final_state.get("flight", "No flight data available"))

        st.subheader("🏨 Hotels")
        st.write(final_state.get("hotel", "No hotel data available"))

        st.subheader("🌦️ Weather Forecast")
        st.write(final_state.get("weather", "No weather data available"))

        st.subheader("🎭 Activities")
        st.write(final_state.get("activities", "No activities data available"))

        with st.expander("📜 Full Workflow State"):
            st.json(final_state)


if __name__ == "__main__":
    main()
