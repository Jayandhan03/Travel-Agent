import streamlit as st
from langgraph.graph import START, StateGraph, END
from agents.agent import TripPlannerAgent, AgentState
from datetime import date
import json

def main():
    """
    Main function to run the Streamlit application.
    This app collects travel details from the user and plans a trip using a LangGraph agent.
    """

    st.set_page_config(page_title="Trip Planner AI", page_icon="✈️", layout="wide")

    st.title("✈️ AI Trip Planner")
    st.markdown("Welcome to the AI Trip Planner! Let's plan your next adventure.")

    # --- User Input Side Bar ---
    with st.sidebar:
        st.header("Your Trip Details")
        
        destination = st.text_input("Enter destination city:", "bali")
        departure = st.text_input("Enter departure city:", "goa")
        trip_start_date = st.date_input("Enter trip start date:", date(2025, 10, 29))
        number_of_days = st.number_input("Enter number of days for the trip:", min_value=1, max_value=30, value=3)
        number_of_people = st.number_input("Enter number of people:", min_value=1, max_value=20, value=3)

        start_planning = st.button("Plan My Trip!", type="primary")

    if start_planning:
        # --- Workflow Execution Area ---
        st.write("### Planning your trip...")
        
        agent = TripPlannerAgent()

        # 1️⃣ Gather input from the user
        user_input = {
            "number_of_days": number_of_days,
            "destination": destination,
            "departure": departure,
            "trip_start_date": trip_start_date.strftime("%Y-%m-%d"),
            "number_of_people": number_of_people,
            "messages": [], "research": [], "weather": [], "flight": [], "hotel": [], "activities": [], "itinerary": [], 
            "next": "", "current_reasoning": ""
        }

        initial_state: AgentState = user_input

        # 2️⃣ Build the workflow graph
        graph = StateGraph(AgentState)
        graph.add_node("supervisor", agent.supervisor_node)
        graph.add_node("research_node", agent.research_node)
        graph.add_node("weather_node", agent.weather_node)
        graph.add_node("flight_node", agent.flight_node)
        graph.add_node("hotel_node", agent.hotel_node)
        graph.add_node("activities_node", agent.activities_node)
        graph.add_node("itinerary_node", agent.itinerary_node)
        graph.add_edge(START, "supervisor")
        app = graph.compile()

        # 3️⃣ Run the workflow
        with st.spinner('Our AI agent is crafting your perfect trip...'):
            final_state = app.invoke(initial_state)

        # 4️⃣ Display final state
        st.success("Your trip has been planned!")
        st.write("---")

        # vvvvvv THIS IS THE MISSING CODE BLOCK THAT YOU NEED TO ADD vvvvvv
        st.header("🎉 Your Personalized Trip Itinerary")
        itinerary_list = final_state.get("itinerary")

        if itinerary_list and isinstance(itinerary_list[0], dict):
            final_plan = itinerary_list[0].get("final_answer")
            if final_plan:
                st.markdown(final_plan)
            else:
                st.warning("The itinerary was generated but appears to be empty.")
        else:
            st.warning("Could not generate a full itinerary.")
        # ^^^^^^ END OF THE MISSING CODE BLOCK ^^^^^^
        
        st.write("---")
        st.header("Trip Details")
        col1, col2 = st.columns(2)

        with col1:
            # --- Display Flight Information ---
            st.subheader("✈️ Flight Information")
            flight_list = final_state.get("flight", [])
            if flight_list:
                try:
                    flight_data = json.loads(flight_list[0].get("final_answer", "{}"))
                    offers = flight_data.get("get_flight_offers_response", {}).get("offers_extracted", [])
                    for offer in offers:
                        st.markdown(f"**Price:** `{offer['price']}`")
                        for i, segment in enumerate(offer['segments']):
                            with st.container(border=True):
                                st.markdown(f"**Leg {i+1}:** `{segment['departure_airport']}` to `{segment['arrival_airport']}`")
                                st.text(f"Departure: {segment['departure_time']}")
                                st.text(f"Arrival:   {segment['arrival_time']}")
                                st.text(f"Carrier: {segment['carrier']} {segment['flight_number']}")
                except (json.JSONDecodeError, KeyError) as e:
                    st.warning("Could not display flight details. Using raw data.")
                    st.json(flight_list)
            else:
                st.info("No flight information available.")

            # --- Display Hotel Information ---
            st.subheader("🏨 Hotel Information")
            hotel_list = final_state.get("hotel", [])
            if hotel_list:
                try:
                    hotel_data = json.loads(hotel_list[0].get("final_answer", "{}"))
                    hotels = hotel_data.get("get_hotels_tool_response", {}).get("output", [])
                    for hotel in hotels:
                        with st.container(border=True):
                            st.markdown(f"**{hotel['name']}**")
                            st.markdown(f"Rating: **{hotel['overall_rating']:.2f}** | Price: **{hotel['price_per_night']}**")
                except (json.JSONDecodeError, KeyError) as e:
                    st.warning("Could not display hotel details. Using raw data.")
                    st.json(hotel_list)
            else:
                st.info("No hotel information available.")

        with col2:
            # --- Display Weather Forecast ---
            st.subheader("🌦️ Weather Forecast")
            weather_list = final_state.get("weather", [])
            if weather_list:
                try:
                    weather_data = weather_list[0].get("final_answer", {})
                    forecast = weather_data.get('forecast', {})
                    if forecast:
                        st.markdown(f"**Location:** {weather_data.get('place', 'N/A').title()}")
                        for i, day in enumerate(forecast.get('time', [])):
                            t_max = forecast['temperature_2m_max'][i]
                            t_min = forecast['temperature_2m_min'][i]
                            precip = forecast['precipitation_sum'][i]
                            with st.container(border=True):
                                st.metric(label=f"**{day}**", value=f"{t_max}°C", delta=f"{t_min}°C (min)")
                                st.markdown(f"Precipitation: `{precip}mm`")
                    else:
                        st.info("No forecast data found in the weather details.")
                except (AttributeError, KeyError) as e:
                    st.warning("Could not display weather details. Using raw data.")
                    st.json(weather_list)
            else:
                st.info("No weather information available.")
                
            # --- Display Activity Suggestions ---
            st.subheader("🎨 Activity Suggestions")
            activity_list = final_state.get("activities", [])
            if activity_list:
                activities = activity_list[0].get("final_answer")
                st.markdown(activities)
            else:
                st.info("No activity suggestions available.")
        
        # Optional: Keep the raw state for debugging, but put it in an expander
        with st.expander("Show Full Workflow State (for debugging)"):
            st.json(final_state)

if __name__ == "__main__":
    main()