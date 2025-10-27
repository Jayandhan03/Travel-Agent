import time
from typing import Any, Optional, List, Dict, Literal
from langgraph.types import Command
from langchain_core.prompts.chat import ChatPromptTemplate,MessagesPlaceholder
from langgraph.graph import END
from langchain.agents import AgentExecutor,create_tool_calling_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from utils.llm_config import LLMModel
from Tools.toolkit import *
from Prompt_template.prompts import hotel_prompt_string,research_prompt,flight_prompt_string,supervisor_prompt,weather_prompt_string,activities_prompt_string,itinerary_prompt_string
from Guardrail.weather_guardrail import *
from Guardrail.flight_guardrail import *
from Guardrail.hotel_guardrail import *
from Guardrail.activities_guardrail import *
from Guardrail.itinerary_guardrail import *
from langchain.output_parsers import PydanticOutputParser,OutputFixingParser
from Guardrail.visa_guardrails import StructuredPlanOutput
from pydantic import BaseModel

class Router(BaseModel):
    next: Literal["research_node","weather_node", "flight_node","hotel_node","activities_node","itinerary_node",END]
    reasoning: str

class AgentState(BaseModel):
    """
    Represents the state of the travel agent, with all fields being optional.
    """
    messages: Optional[List[Any]] = None
    number_of_days: Optional[int] = None
    destination: Optional[str] = None
    departure: Optional[str] = None
    trip_start_date: Optional[str] = None
    number_of_people: Optional[int] = None
    research: Optional[List[Dict[str, Any]]] = None
    weather: Optional[Any] = None
    flight: Optional[Any] = None
    hotel: Optional[Any] = None
    activities: Optional[Any] = None
    itinerary: Optional[Any] = None
    next: Optional[str] = None
    current_reasoning: Optional[str] = None

class TripPlannerAgent:
    def __init__(self):
        self.llm_model = LLMModel

    def supervisor_node(self,state:AgentState) -> Command[Literal["research_node","weather_node", "flight_node","hotel_node","activities_node","itinerary_node",END]]:
        state_summary = (
        f"Current Workflow Status:\n"
        f"- Visa research Generated: {'Yes' if state.research else 'No'}\n"
        f"- If weather details Generated: {'Yes' if state.weather else 'No'}\n"
        f"- If flight details Generated: {'Yes' if state.flight else 'No'}\n"
        f"- If hotel details Generated: {'Yes' if state.hotel else 'No'}\n"
        f"- If activities details Generated: {'Yes' if state.activities else 'No'}\n"
        f"- If itinerary Generated: {'Yes' if state.itinerary else 'No'}\n" 
    )

        messages_for_llm = [
            SystemMessage(content=supervisor_prompt),
            HumanMessage(content=state_summary),
        ]

        print("***********************Invoking LLM for routing decision************************")

        parser = PydanticOutputParser(pydantic_object=Router)

        fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=self.llm_model)

        chain = self.llm_model | fixing_parser
        
        # Add retries
        max_attempts = 3
        attempt = 0
        error_msg = None
        response = None

        while attempt < max_attempts:
            attempt += 1
            print(f"--- Attempt {attempt} ---")

            # Compose messages for this attempt
            messages_for_this_attempt = list(messages_for_llm)

            if error_msg:
                # Inject previous error info to let LLM know what failed
                messages_for_this_attempt.append(HumanMessage(content=f"Previous attempt failed due to: {error_msg}. Please follow the schema strictly: {Router.model_json_schema()}"))

            try:
                response = chain.invoke(messages_for_this_attempt)
                break
            
            except Exception as e:
                error_msg = str(e)
                print(f"--- Error on attempt {attempt}: {error_msg} ---")
                # If last attempt, will exit loop and propagate error

        if response is None:
            # All retries failed, fallback error
            fallback_msg = f"All {max_attempts} attempts failed. Last error: {error_msg}"
            print(f"--- Supervisor node failed ---\n{fallback_msg}")
            return Command(
                goto="END",
                update={
                    "next": "END",
                    "current_reasoning": fallback_msg
                }
            )
        
        goto = response.next
        
        print("********************************this is my goto*************************")

        print(goto)
        
        print(response.reasoning)
            
        if goto == "END":
            goto = END 
            
        print("**************************below is my state****************************")

        print(state)
        
        return Command(goto=goto, update={'next': goto, 
                                        'current_reasoning': response.reasoning}
                    )
    

    def research_node(self, state: AgentState) -> Command[Literal['supervisor']]:

        print("*****************called research node************")

        destination = state.destination

        departure = state.departure

        nationality = "Indian"

        parser = PydanticOutputParser(pydantic_object=StructuredPlanOutput)

        fixing_parser = OutputFixingParser.from_llm(parser=parser, llm=self.llm_model)

        task_prompt = (
        f"Find the visa requirements for a citizen with a {nationality} passport "
        f"traveling to {destination} from {departure}."
    )
        print(f"--- Sending this direct task to the agent ---\n{task_prompt}\n---------------------------------------------")

        system_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", research_prompt), 
            ("human", "{messages}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")  
        ]
    )

        research_agent = create_tool_calling_agent(
            llm=self.llm_model,
            tools=[fetch_visa_info],
            prompt=system_prompt
        )

        agent_executor = AgentExecutor(
            agent=research_agent,
            tools=[fetch_visa_info],
            verbose=True,
            handle_parsing_errors="Please try again, paying close attention to the required tool arguments."
        )

        # 5. Wrap execution in a retry loop
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                result = agent_executor.invoke({"messages": [HumanMessage(content=task_prompt)],
            "chat_history": []})

                # Try parsing the final output
                final_output_string = result.get("output", "")

                parsed_output: StructuredPlanOutput = fixing_parser.parse(final_output_string)

                summary_str = f"{parsed_output.summary}\n{parsed_output.details}"

                # Update state and return
                return Command(
                    update={
                        "messages": [
                            AIMessage(content=summary_str, name="research_node")
                        ],
                        "research": [{"final_answer": summary_str}]
                    },
                    goto="supervisor",
                )

            except Exception as e:
                error_msg = (
                    f"Attempt {attempt} failed due to error: {str(e)}. "
                    f"Please strictly follow the schema: {StructuredPlanOutput.model_json_schema()}"
                )
                print(f"--- Runtime/Parsing error encountered ---\n{error_msg}")
                # Inject error into prompt for next retry
                # Use an f-string to properly embed all variables
                task_prompt = f"The previous attempt failed with this error: {error_msg}. Please correct your tool usage and try again. Here is the original task:\n---\n{task_prompt}"

        # If all attempts fail, fallback to supervisor with error message
        return Command(
            update={
                "messages": [
                    AIMessage(content="Error: The analysis agent failed to produce visa details after multiple attempts.", 
                            name="research_Error")
                ],
                "research": [{"error": "Parsing failed after retries"}]
            },
            goto="supervisor",
        )

    def weather_node(self, state: AgentState) -> Command[Literal['supervisor']]:

        print("*****************called weather node************")
       
        destination= state.destination

        trip_start_date= state.trip_start_date

        number_of_days= state.number_of_days
        
        weather_task_prompt = (
        f"""Find the weather condition for this destination {destination} ,trip starting from {trip_start_date}
        for {number_of_days} days by using the get_weather tool and return as a dict with summary and details keys."""
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
            MessagesPlaceholder(variable_name="agent_scratchpad") 
            ]
        )

        weather_agent = create_tool_calling_agent(
            llm=self.llm_model,
            tools=[get_weather], 
            prompt=system_prompt
        )
        agent_executor = AgentExecutor(
            agent=weather_agent,
            tools=[get_weather],
            verbose=True,
            handle_parsing_errors="Please try again, paying close attention to the required tool arguments."
        )

        # 5. Wrap execution in a retry loop
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                result = agent_executor.invoke({"messages": [HumanMessage(content=weather_task_prompt)],
            "chat_history": []})

                # Try parsing the final output
                final_output_string = result.get("output", "")

                # Update state and return
                return Command(
                    update={
                        "messages": [
                            AIMessage(content=str(final_output_string), name="weather_node")
                        ],
                        "weather": [{"final_answer": final_output_string}]
                    },
                    goto="supervisor",
                )

            except Exception as e:
                error_msg = (
                    f"Attempt {attempt} failed due to error: {str(e)}. "
                    # f"Please strictly follow the schema: {WeatherSummary.model_json_schema()}"
                )
                print(f"--- Runtime/Parsing error encountered ---\n{error_msg}")
                # Inject error into prompt for next retry
                # Use an f-string to properly embed all variables
                weather_task_prompt = f"The previous attempt failed with this error: {error_msg}. Please correct your tool usage and try again. Here is the original task:\n---\n{weather_task_prompt}"

        # If all attempts fail, fallback to supervisor with error message
        return Command(
            update={
                "messages": [
                    AIMessage(content="Error: The analysis agent failed to produce visa details after multiple attempts.", 
                            name="weather_Error")
                ],
                "weather": [{"error": "Parsing failed after retries"}]
            },
            goto="supervisor",
        )


    def flight_node(self, state: AgentState) -> Command[Literal['supervisor']]:

        print("*****************called flight node************")
        
        departure= state.departure
        destination= state.destination
        trip_start_date= state.trip_start_date

        flight_task_prompt = f""" Find the available flights from {departure} to {destination} for {trip_start_date} call the tool 
        with the correct departure and destination code IDs for the given destination and departure date"""
        
        # Simple system prompt like weather_node
        system_prompt = ChatPromptTemplate.from_messages([
            ("system",flight_prompt_string),
            ("user", "{messages}"),
            MessagesPlaceholder(variable_name="agent_scratchpad") 
        ])

        flight_agent = create_tool_calling_agent(
            llm=self.llm_model,
            tools=[get_flight_offers],
            prompt=system_prompt
        )
        agent_executor = AgentExecutor(
            agent=flight_agent,
            tools=[get_flight_offers],
            verbose=True,
            handle_parsing_errors="Please try again, paying close attention to the required tool arguments."
        )

        # 5. Wrap execution in a retry loop
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                result = agent_executor.invoke({"messages": [HumanMessage(content=flight_task_prompt)],
            "chat_history": []})

                # Try parsing the final output
                final_output_string = result.get("output", "")

                # Update state and return
                return Command(
                    update={
                        "messages": [
                            AIMessage(content=str(final_output_string), name="flight_node")
                        ],
                        "flight": [{"final_answer": final_output_string}]
                    },
                    goto="supervisor",
                )

            except Exception as e:
                error_msg = (
                    f"Attempt {attempt} failed due to error: {str(e)}. "
                    # f"Please strictly follow the schema: {WeatherSummary.model_json_schema()}"
                )
                print(f"--- Runtime/Parsing error encountered ---\n{error_msg}")
                # Inject error into prompt for next retry
                # Use an f-string to properly embed all variables
                flight_task_prompt = f"The previous attempt failed with this error: {error_msg}. Please correct your tool usage and try again. Here is the original task:\n---\n{flight_task_prompt}"

        # If all attempts fail, fallback to supervisor with error message
        return Command(
            update={
                "messages": [
                    AIMessage(content="Error: The analysis agent failed to produce visa details after multiple attempts.", 
                            name="flight_Error")
                ],
                "flight": [{"error": "Parsing failed after retries"}]
            },
            goto="supervisor",
        )
    

    def hotel_node(self,state:AgentState) -> Command[Literal['supervisor']]:

        print("*****************called hotel node************")
  
        destination=state.destination
        number_of_days=state.number_of_days
        trip_start_date=state.trip_start_date

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
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ]
    )

        hotel_agent = create_tool_calling_agent(llm=self.llm_model,tools=[get_hotels_tool] ,prompt=system_prompt)

        agent_executor = AgentExecutor(
            agent=hotel_agent,
            tools=[get_hotels_tool],
            verbose=True,
            handle_parsing_errors="Please try again, paying close attention to the required tool arguments."
        )

        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                result = agent_executor.invoke({"messages": [HumanMessage(content=hotel_task_prompt)],
            "chat_history": []})

                final_output_string = result.get("output", "")

                return Command(
                    update={
                        "messages": [
                            AIMessage(content=str(final_output_string), name="hotel_node")
                        ],
                        "hotel": [{"final_answer": final_output_string}]
                    },
                    goto="supervisor",
                )

            except Exception as e:
                error_msg = (
                    f"Attempt {attempt} failed due to error: {str(e)}. "
                    # f"Please strictly follow the schema: {WeatherSummary.model_json_schema()}"
                )
                print(f"--- Runtime/Parsing error encountered ---\n{error_msg}")
                # Inject error into prompt for next retry
                # Use an f-string to properly embed all variables
                hotel_task_prompt = f"The previous attempt failed with this error: {error_msg}. Please correct your tool usage and try again. Here is the original task:\n---\n{hotel_task_prompt}"

        # If all attempts fail, fallback to supervisor with error message
        return Command(
            update={
                "messages": [
                    AIMessage(content="Error: The analysis agent failed to produce visa details after multiple attempts.", 
                            name="weather_Error")
                ],
                "hotel": [{"error": "Parsing failed after retries"}]
            },
            goto="supervisor",
        )

    
    def activities_node(self,state:AgentState) -> Command[Literal['supervisor']]:

        print("*****************called activities node************")

        destination=state.destination
        number_of_days=state.number_of_days
        trip_start_date=state.trip_start_date

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
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ]
    )

        activities_agent = create_tool_calling_agent(llm=self.llm_model,tools=[get_activities_opentripmap] ,prompt=system_prompt)
        
        agent_executor = AgentExecutor(
            agent=activities_agent,
            tools=[get_activities_opentripmap],
            verbose=True,
            handle_parsing_errors="Please try again, paying close attention to the required tool arguments."
        )

        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                result = agent_executor.invoke({"messages": [HumanMessage(content=activities_task_prompt)],
            "chat_history": []})

                final_output_string = result.get("output", "")

                return Command(
                    update={
                        "messages": [
                            AIMessage(content=str(final_output_string), name="activities_node")
                        ],
                        "activities": [{"final_answer": final_output_string}]
                    },
                    goto="supervisor",
                )

            except Exception as e:
                error_msg = (
                    f"Attempt {attempt} failed due to error: {str(e)}. "
                    # f"Please strictly follow the schema: {WeatherSummary.model_json_schema()}"
                )
                print(f"--- Runtime/Parsing error encountered ---\n{error_msg}")
                # Inject error into prompt for next retry
                # Use an f-string to properly embed all variables
                activities_task_prompt = f"The previous attempt failed with this error: {error_msg}. Please correct your tool usage and try again. Here is the original task:\n---\n{activities_task_prompt}"

        # If all attempts fail, fallback to supervisor with error message
        return Command(
            update={
                "messages": [
                    AIMessage(content="Error: The analysis agent failed to produce visa details after multiple attempts.", 
                            name="activities_Error")
                ],
                "activities": [{"error": "Parsing failed after retries"}]
            },
            goto="supervisor",
        )
    
    def itinerary_node(self, state: AgentState) -> Command[Literal['supervisor']]:

        print("*****************called itinerary node************")

        research= state.research
        weather=state.weather
        hotel=state.hotel
        activities= state.activities
        destination=state.destination
        departure=state.departure
        number_of_days=state.number_of_days
        trip_start_date=state.trip_start_date
        flight=state.flight

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
            MessagesPlaceholder(variable_name="agent_scratchpad")
            ]
        )

        # Replace tool with itinerary generator (if you have one)
        itinerary_agent = create_tool_calling_agent(
            llm=self.llm_model,
            tools=[],
            prompt=system_prompt
        )

        agent_executor = AgentExecutor(
            agent=itinerary_agent,
            tools=[get_activities_opentripmap],
            verbose=True,
            handle_parsing_errors="Please try again, paying close attention to the required tool arguments."
        )

        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            attempt += 1
            try:
                result = agent_executor.invoke({"messages": [HumanMessage(content=itinerary_task_prompt)],
            "chat_history": []})

                final_output_string = result.get("output", "")

                return Command(
                    update={
                        "messages": [
                            AIMessage(content=str(final_output_string), name="itinerary_node")
                        ],
                        "itinerary": [{"final_answer": final_output_string}]
                    },
                    goto="supervisor",
                )

            except Exception as e:
                error_msg = (
                    f"Attempt {attempt} failed due to error: {str(e)}. "
                    # f"Please strictly follow the schema: {WeatherSummary.model_json_schema()}"
                )
                print(f"--- Runtime/Parsing error encountered ---\n{error_msg}")
                # Inject error into prompt for next retry
                # Use an f-string to properly embed all variables
                itinerary_task_prompt = f"The previous attempt failed with this error: {error_msg}. Please correct your tool usage and try again. Here is the original task:\n---\n{itinerary_task_prompt}"

        # If all attempts fail, fallback to supervisor with error message
        return Command(
            update={
                "messages": [
                    AIMessage(content="Error: The analysis agent failed to produce visa details after multiple attempts.", 
                            name="itinerary_Error")
                ],
                "itinerary": [{"error": "Parsing failed after retries"}]
            },
            goto="supervisor",
        )
