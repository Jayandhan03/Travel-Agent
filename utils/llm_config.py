import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()  # loads from .env file

LLMModel = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY")
)

# def research_node(self, state: AgentState) -> Command[Literal['supervisor']]:
#         print("*****************called research node************")

#         destination = state.get("destination")

#         departure = state.get("departure")

#         nationality = "Indian"

#         task_prompt = (
#         f"Find the visa requirements for a citizen with a {nationality} passport "
#         f"traveling to {destination} from {departure}."
#     )
#         print(f"--- Sending this direct task to the agent ---\n{task_prompt}\n---------------------------------------------")

#         system_prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", research_prompt), 
#             ("user", "{messages}"),
#         ]
#     )

#         last_five = state["messages"][-1:] 

#         research_agent = create_react_agent(
#             model=self.llm_model,
#             tools=[fetch_visa_info],
#             prompt=system_prompt
#         )

#         result = research_agent.invoke({"messages": [HumanMessage(content=task_prompt)]})

#         tool_output = None
       
#         if result.get("intermediate_steps"):
#             tool_output = result["intermediate_steps"][-1][1]
#         else:
#             tool_output = result.get("output", "No detailed output was generated.")

#         # Summarize the raw tool output for clean state management.
#         parsed = summarize_tool_output(tool_output, self.llm_model)

#         print("--- Research complete, updating state and returning to supervisor ---")

#         return Command(
#             update={
#                 "messages": state["messages"][-1:] + [
#                     AIMessage(
#                         content=parsed.summary,
#                         name="research_node"
#                     )
#                 ],
#                 "research": parsed.details
#             },
#             goto="supervisor",
#         )