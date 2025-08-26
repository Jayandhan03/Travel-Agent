from typing import Literal,Any
from langgraph.types import Command
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict, Annotated
from langchain_core.prompts.chat import ChatPromptTemplate
from langgraph.graph import START, StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from utils.llm_config import LLMModel
from Tools.toolkit import *
from Prompt_template.prompts import supervisor_prompt,research_prompt
from typing import Any, TypedDict
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
import json,re
from copy import deepcopy

class Router(TypedDict):
    next: Literal["research_node","weather_node", "flight_node","hotel_node","activities_node","itirnerary_node",END]
    reasoning: str

class AgentState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    number_of_days: int
    destination: str
    departure: str
    trip_start_date: str
    number_of_people: int
    id_number: str
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

    def supervisor_node(self,state:AgentState) -> Command[Literal["research_node","weather_node", "flight_node","hotel_node","activities_node","itirnerary_node",END]]:
        print("**************************below is my state right after entering****************************")
        print(state)

        serializable_state = deepcopy(state)

        if "messages" in serializable_state and serializable_state["messages"]:
            serializable_state['messages'] = [msg.dict() for msg in serializable_state['messages']]

        user_content_with_state = f"Current state:\n{json.dumps(serializable_state, indent=2)}"
        
        messages_for_llm = [
            SystemMessage(content=supervisor_prompt),
            HumanMessage(content=user_content_with_state),
        ]
        
        messages_for_llm.extend(state["messages"][-5:])

        print("***********************this is my message*****************************************")
        print(messages_for_llm)
        
        response = self.llm_model.with_structured_output(Router).invoke(messages_for_llm)
        
        goto = response["next"]
        
        print("********************************this is my goto*************************")
        print(goto)
        
        print("********************************")
        print(response["reasoning"])
            
        if goto == "FINISH":
            goto = END
            
        print("**************************below is my state****************************")
        print(state)
        
        return Command(goto=goto, update={'next': goto, 
                                        'current_reasoning': response["reasoning"]}
                    )
    

    def research_node(self,state:AgentState) -> Command[Literal['supervisor']]:
        print("*****************called research node************")

        state_json = json.dumps(state, default=str).replace("{", "{{").replace("}", "}}")
                       
        system_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"Current full state (as JSON dict for reference): {state_json}\n\n" + research_prompt
            ),
            (
                "user",
                "{messages}"  
            ),
        ]
    )
        
        last_five = state["messages"][-5:] if len(state["messages"]) > 5 else state["messages"]

        research_agent = create_react_agent(model=self.llm_model,tools=[fetch_visa_info] ,prompt=system_prompt)
        
        result = research_agent.invoke({
        "messages": last_five
    })
        clean_text = result["messages"][-1].content.strip()

        clean_text = re.sub(r'[\{\}"\\]', '', clean_text)  # remove { } " \
        clean_text = clean_text.replace("\n", " ").replace("\r", " ")  # remove newlines
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return Command(
    update={
        "messages": state["messages"] + [
            AIMessage(
                content=clean_text,
                name="research_node"
            )
        ],
        "research": clean_text 
    },
    goto="supervisor",
)
