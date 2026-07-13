import os
import datetime
import asyncio
from typing import List, Annotated, TypedDict

# --- Third-Party Imports ---
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain_community.tools import TavilySearchResults

# --- LangGraph Imports ---
from langgraph.graph import StateGraph, START
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# ==========================================
# 1. CONFIGURATION & INITIALIZATION
# ==========================================
load_dotenv()

# Initialize the LLM (Groq in this case)
llm = ChatGroq(
    model=os.getenv('GROQ_MODEL'), 
    api_key=os.getenv('GROQ_API_KEY')
)

# Initialize the search tool
search_tool = TavilySearchResults(api_key=os.getenv('TAVILY_API_KEY'))
tools = [search_tool]

# Bind tools to the LLM so it knows what JSON schemas it can output to trigger them
llm_with_tools = llm.bind_tools(tools)

current_date = datetime.date.today()


# ==========================================
# 2. STATE DEFINITION
# ==========================================
# TypedDict defines the structure of our graph's state.
# PEP 8 standard dictates class names should be CamelCase.
class ChatState(TypedDict):
    # Annotated tells LangGraph HOW to update this key. 
    # add_messages is a built-in reducer that intelligently appends new messages 
    # rather than overwriting the entire list.
    messages: Annotated[List[BaseMessage], add_messages]


# ==========================================
# 3. GRAPH NODES (The Agents)
# ==========================================
async def chat_session(state: ChatState):
    """
    The main reasoning node. It takes the current state, formats a prompt 
    with a system message and chat history, and asks the LLM to respond.
    """

    # System prompt injected at the beginning of every LLM call
    system_prompt = SystemMessage(
        f'You are a helpful web search assistant tasked with responding to user questions '
        f'using the tool list available at your disposal based on information available till {current_date}. '
        f'Provide only relevant information in response, minimizing token usage STRICTLY.'
    )
    
    # Combine system prompt with existing chat history from the state
    prompt = [system_prompt] + state['messages']

    # Invoke the LLM asynchronously
    response = await llm_with_tools.ainvoke(prompt)

    # Return the new message to be appended to the state by the reducer
    return {'messages': [response]}


# ==========================================
# 4. GRAPH CONSTRUCTION (The Workflow)
# ==========================================
# ToolNode is a pre-built LangGraph node that executes tool calls based on 
# the AIMessage's tool_calls property.
tool_node = ToolNode(tools)

# InMemorySaver allows the graph to remember state across multiple invokes 
# (e.g., remembering the previous question in a while loop).
checkpointer = InMemorySaver()

# Initialize the StateGraph with our defined state schema
graph = StateGraph(ChatState)

# Add the logic nodes
graph.add_node('chat_session', chat_session)
graph.add_node('tools', tool_node)

# Define the edges (routing logic)
graph.add_edge(START, 'chat_session') 

# tools_condition is a pre-built conditional edge that checks if the last 
# AIMessage contains tool_calls. If yes -> go to 'tools'. If no -> go to END.
graph.add_conditional_edges('chat_session', tools_condition)

# After tools execute, always route back to the LLM so it can process the tool results
graph.add_edge('tools', 'chat_session')

# Compile the graph into an executable workflow, passing the checkpointer
workflow = graph.compile(checkpointer=checkpointer)


# ==========================================
# 5. EXECUTION LOOP (The Interface)
# ==========================================
# A thread ID is required by the checkpointer to segregate memory. 
# If you changed this ID, it would start a brand new conversation.
thread_id = 1
config = {'configurable': {'thread_id': thread_id}}

async def main():
    print("Chatbot initialized. Type 'exit', 'quit', or 'shutdown' to stop.\n")
    
    while True:
        user_query = input("Query: ").strip()

        # Exit conditions
        if user_query in ['close', 'quit', 'exit', 'shutdown']:
            print("Shutting down...")
            break
        
        # Prevent sending empty API requests if user just hits Enter
        if not user_query:
            continue

        # Format the input to match the ChatState schema
        user_input = {'messages': [HumanMessage(user_query)]}

        # Wrap the graph execution in a try/except to prevent 
        # ugly tracebacks from crashing the loop on API errors/rate limits
        try:
            output = await workflow.ainvoke(user_input, config=config)
            
            # The last message in the output list is the final AI response 
            # (after any intermediate tool loops have finished)
            print(f"Response: {output['messages'][-1].content}\n")
            
        except Exception as e:
            print(f"An error occurred while processing your request: {e}\n")


# Standard Python entry point. 
# Note: If you run this .py file *inside* a Jupyter cell using %run or !python, 
# and get "Event loop is closed" errors, change `asyncio.run(main())` to `await main()`
if __name__ == '__main__':
    asyncio.run(main())