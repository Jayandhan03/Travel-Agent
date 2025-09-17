from typing import Literal,Any
from langgraph.types import Command
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated
from langchain_core.prompts.chat import ChatPromptTemplate
from langgraph.graph import END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from utils.llm_config import LLMModel
from Tools.toolkit import *
from Prompt_template.prompts import hotel_prompt_string,research_prompt,flight_prompt_string,supervisor_prompt,weather_prompt_string,activities_prompt_string,itinerary_prompt_string
from typing import Any, TypedDict
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
import json
from Guardrail.Visa_guardrail import *
from Guardrail.weather_guardrail import *
from Guardrail.flight_guardrail import *
from Guardrail.hotel_guardrail import *
from Guardrail.activities_guardrail import *
from Guardrail.itinerary_guardrail import *

class Router(TypedDict):
    next: Literal["research_node","weather_node", "flight_node","hotel_node","activities_node","itinerary_node","human_feedback_node",END]
    reasoning: str

class AgentState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    number_of_days: int
    destination: str
    departure: str
    trip_start_date: str
    number_of_people: int
    research: dict[str, Any]
    weather: dict[str, Any]
    flight: dict[str, Any]
    hotel: dict[str, Any]
    activities: dict[str, Any]
    itinerary: dict[str, Any]
    next: str
    current_reasoning: str

class TripPlannerAgent:
    def __init__(self):
        self.llm_model = LLMModel

    def supervisor_node(self,state:AgentState) -> Command[Literal["research_node","weather_node", "flight_node","hotel_node","activities_node","itinerary_node","human_feedback_node",END]]:
        print("**************************below is my state right after entering****************************")
        print(state)

        ROUTING_KEYS = [
            "research", "weather", "flight", "hotel", "activities", "itinerary"
        ]

        supervisor_context = {
            key: bool(state.get(key)) for key in ROUTING_KEYS
        }

        user_content_with_state = f"Current task completion state:\n{json.dumps(supervisor_context, indent=2)}"
        print(f"--- Sending this minimal context to the LLM ---\n{user_content_with_state}\n-------------------------------------------------")
        
        messages_for_llm = [
            SystemMessage(content=supervisor_prompt),
            HumanMessage(content=user_content_with_state),
        ]
        
        if state.get("messages"):
            last_message = state["messages"][-1]
            messages_for_llm.append(last_message)
            print(f"--- Attaching last message ---\nType: {type(last_message).__name__}\nContent: {last_message.content}\n----------------------------------")

        print("***********************Invoking LLM for routing decision************************")
        
        response = self.llm_model.with_structured_output(Router).invoke(messages_for_llm)
        
        goto = response["next"]
        
        print("********************************this is my goto*************************")
        print(goto)
        
        print("********************************")
        print(response["reasoning"])
            
        if goto == "END":
            goto = "__end__" 
            
        print("**************************below is my state****************************")
        print(state)
        
        return Command(goto=goto, update={'next': goto, 
                                        'current_reasoning': response["reasoning"]}
                    )
    

    def research_node(self, state: AgentState) -> Command[Literal['supervisor']]:
        print("*****************called research node************")

        destination = state.get("destination")

        departure = state.get("departure")

        nationality = "Indian"

        task_prompt = (
        f"Find the visa requirements for a citizen with a {nationality} passport "
        f"traveling to {destination} from {departure}."
    )
        print(f"--- Sending this direct task to the agent ---\n{task_prompt}\n---------------------------------------------")

        system_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", research_prompt), 
            ("user", "{messages}"),
        ]
    )

        research_agent = create_react_agent(
            model=self.llm_model,
            tools=[fetch_visa_info],
            prompt=system_prompt
        )

        result = research_agent.invoke({"messages": [HumanMessage(content=task_prompt)]})

        # 🔑 Get the last tool observation (structured JSON output)
        tool_output = None
        if "intermediate_steps" in result:
            # intermediate_steps is usually [(AgentAction, observation), ...]
            tool_output = result["intermediate_steps"][-1][1]
        else:
            # fallback to final message content
            tool_output = result["messages"][-1].content

        # 🔑 Summarize JSON output with schema guardrail
        parsed = summarize_tool_output(tool_output, self.llm_model)

        return Command(
            update={
                "messages": state["messages"][-1:] + [
                    AIMessage(
                        content=parsed.summary,
                        name="research_node"
                    )
                ],
                "research": parsed.details
            },
            goto="supervisor",
        )


    def weather_node(self, state: AgentState) -> Command[Literal['supervisor']]:
        print("*****************called weather node************")

       
        destination= state.get("destination")
        trip_start_date= state.get("trip_start_date")
        number_of_days= state.get("number_of_days")
        
        weather_task_prompt = (
        f"""Find the weather condition for this destination {destination} ,trip starting from {trip_start_date}
        for {number_of_days} days by using the get_weather tool."""
    )
        print(f"--- Sending this direct task to the agent ---\n{weather_task_prompt}\n---------------------------------------------")

        system_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system", weather_prompt_string
                ),
                (
                    "user",
                    "{messages}"
                ),
            ]
        )

        weather_agent = create_react_agent(
            model=self.llm_model,
            tools=[get_weather], 
            prompt=system_prompt
        )
        result = weather_agent.invoke({"messages": weather_task_prompt})

        # Extract JSON tool output
        if "intermediate_steps" in result:
            tool_output = result["intermediate_steps"][-1][1]
        else:
            tool_output = result["messages"][-1].content

        # Run schema-based summarizer
        parsed = summarize_weather_output(tool_output, self.llm_model)

        return Command(
            update={
                "messages": state["messages"][-1:] + [
                    AIMessage(
                        content=parsed.summary,
                        name="weather_node"
                    )
                ],
                "weather": parsed.details
            },
            goto="supervisor",
        )


    def flight_node(self, state: AgentState) -> Command[Literal['supervisor']]:
        print("*****************called flight node************")

        
        departure= state.get("departure")
        destination= state.get("destination")
        trip_start_date= state.get("trip_start_date")

        flight_task_prompt = f""" Find the available flights from {departure} to {destination} for {trip_start_date}"""
        
        # Simple system prompt like weather_node
        system_prompt = ChatPromptTemplate.from_messages([
            ("system",flight_prompt_string),
            ("user", "{messages}")
        ])

        flight_agent = create_react_agent(
            model=self.llm_model,
            tools=[get_flight_offers],
            prompt=system_prompt
        )
        result = flight_agent.invoke({
    "messages": [
        HumanMessage(content=f"Flight search context: {flight_task_prompt}")
    ]
})


        # Extract tool output (JSON from get_flight_offers)
        if "intermediate_steps" in result:
            tool_output = result["intermediate_steps"][-1][1]
        else:
            tool_output = result["messages"][-1].content

        # Run schema-based summarizer
        parsed = summarize_flight_output(tool_output, self.llm_model)

        return Command(
            update={
                "messages": state["messages"][-1:] + [
                    AIMessage(
                        content=parsed.summary,
                        name="flight_node"
                    )
                ],
                "flight": parsed.details
            },
            goto="supervisor",
        )
    

    def hotel_node(self,state:AgentState) -> Command[Literal['supervisor']]:
        print("*****************called hotel node************")

  
        destination=state.get("destination")
        number_of_days=state.get("number_of_days")
        trip_start_date=state.get("trip_start_date")

        hotel_task_prompt = f"""Find available hotels in {destination} for {number_of_days} days starting from {trip_start_date}"""
                       
        system_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",hotel_prompt_string
            ),
            (
                "user",
                "{messages}"  
            ),
        ]
    )

        hotel_agent = create_react_agent(model=self.llm_model,tools=[get_hotels_tool] ,prompt=system_prompt)
        
        result = hotel_agent.invoke({
        "messages": hotel_task_prompt
    })
        tool_output = None
        if "intermediate_steps" in result:
            # intermediate_steps is usually [(AgentAction, observation), ...]
            tool_output = result["intermediate_steps"][-1][1]
        else:
            # fallback to final message content
            tool_output = result["messages"][-1].content

        # 🔑 Summarize JSON output with schema guardrail
        parsed = summarize_hotel_output(tool_output, self.llm_model)
        
        return Command(
    update={
        "messages": state["messages"][-1:] + [
            AIMessage(
                content=parsed.summary,
                name="hotel_node"
            )
        ],
        "hotel": parsed.details
    },
    goto="supervisor",
)
    
    def activities_node(self,state:AgentState) -> Command[Literal['supervisor']]:
        print("*****************called activities node************")

        destination=state.get("destination")
        number_of_days=state.get("number_of_days")
        trip_start_date=state.get("trip_start_date")

        activities_task_prompt = f"""Find activities in {destination} for {number_of_days} days starting from {trip_start_date}"""    
                       
        system_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",activities_prompt_string
            ),
            (
                "user",
                "{messages}"  
            ),
        ]
    )

        activities_agent = create_react_agent(model=self.llm_model,tools=[get_activities_opentripmap] ,prompt=system_prompt)
        
        result = activities_agent.invoke({
        "messages": activities_task_prompt
    })
        tool_output = None
        if "intermediate_steps" in result:
            # intermediate_steps is usually [(AgentAction, observation), ...]
            tool_output = result["intermediate_steps"][-1][1]
        else:
            # fallback to final message content
            tool_output = result["messages"][-1].content

        # 🔑 Summarize JSON output with schema guardrail
        parsed = summarize_activities_output(tool_output, self.llm_model)
        
        return Command(
    update={
        "messages": state["messages"][-1:] + [
            AIMessage(
                content=parsed.summary,
                name="activities_node"
            )
        ],
        "activities": parsed.details
    },
    goto="supervisor",
)
    
    def itinerary_node(self, state: AgentState) -> Command[Literal['supervisor']]:
        print("*****************called itinerary node************")

        research= state.get("research")
        weather=state.get("weather")
        hotel=state.get("hotel")
        activities= state.get("activities")
        destination=state.get("destination")
        departure=state.get("departure")
        number_of_days=state.get("number_of_days")
        trip_start_date=state.get("trip_start_date")
        flight=state.get("flight")

        itinerary_task_prompt = f"""
        Prepare a travel itinerary. 

        Start by giving visa and entry details based on: {research}.  
        Then describe the expected weather: {weather}.  
        After that, suggest flights from {departure} to {destination} on {trip_start_date}: {flight}.  
        Next, recommend hotels to check in: {hotel}.  
        Finally, plan day-by-day activities for {number_of_days} days using: {activities}.  

        End with a short summary of the trip.
        """
        
        system_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",itinerary_prompt_string
                ),
                (
                    "user",
                    "{messages}"
                ),
            ]
        )

        # Replace tool with itinerary generator (if you have one)
        itinerary_agent = create_react_agent(
            model=self.llm_model,
            tools=[],
            prompt=system_prompt
        )

        result = itinerary_agent.invoke({
            "messages": itinerary_task_prompt
        })

        tool_output = None
        if "intermediate_steps" in result:
            # intermediate_steps is usually [(AgentAction, observation), ...]
            tool_output = result["intermediate_steps"][-1][1]
        else:
            # fallback to final message content
            tool_output = result["messages"][-1].content

        # 🔑 Summarize JSON output with schema guardrail
        parsed = summarize_itinerary_output(tool_output, self.llm_model)

        return Command(
            update={
                "messages": state["messages"][-1:] + [
                    AIMessage(
                        content=parsed.summary,
                        name="itinerary_node"
                    )
                ],
                "itinerary": parsed.details
            },
            goto="supervisor",
        )

    def human_feedback_node(self,state: AgentState) -> Command[Literal['supervisor']]:
        print("\n=== HUMAN IN THE LOOP ===")
        print("Supervisor wants your feedback on the plan so far:\n")
        print(state.get("messages")[-1].content)  # show last agent reply

        user_input = input("Your feedback (or type 'ok' to approve): ")

        return Command(
            update={
                "messages": state["messages"][-1:] + [
                    HumanMessage(content=user_input, name="human")
                ],
                "human_feedback": user_input
            },
            goto="supervisor" 
        )
