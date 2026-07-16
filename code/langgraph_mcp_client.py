import os
import asyncio
from typing import Annotated, List, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, BaseMessage

# Modern LangGraph Imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

# MCP Adapters
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# 1. Define State (Fix: BaseMessage, not str)
class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


async def main():
    # Initialize LLM
    llm = ChatGroq(model=os.getenv('GROQ_MODEL'), api_key=os.getenv('GROQ_API_KEY'))
    
    config = {'configurable': {'thread_id': 1}}
    
    math_server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "langgraph_mcp_math_server.py")
    # 2. MCP Context Manager
    # This keeps the stdio subprocess alive and manages the HTTP connection
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "stdio",
                "command": "python",
                "args": [math_server_path]
            },
            "weather": {
                "transport": "streamable-http",
                "url": "http://localhost:8000/mcp"
            }
        }
    )
        
        # Await the tools properly
    tools = await client.get_tools()
    
    # 3. Bind tools to LLM (The modern LangGraph way, no legacy create_agent)
    llm_with_tools = llm.bind_tools(tools)

    # 4. Define the chat node
    async def chatbot(state: ChatState):

        response = await llm_with_tools.ainvoke(state['messages'])
        
        return {"messages": [response]}

    # 5. Build the Graph with a proper Tool Loop
    tool_node = ToolNode(tools)
    checkpointer = InMemorySaver()
    
    graph = StateGraph(ChatState)
    
    graph.add_node("chatbot", chatbot)
    graph.add_node("tools", tool_node)
    
    # Use constants, not strings
    graph.add_edge(START, "chatbot")
    
    # This automatically routes to "tools" if the LLM makes a tool call, 
    # or to END if it just generates text
    graph.add_conditional_edges("chatbot", tools_condition)
    
    # After tools run, go back to the chatbot to process the tool output
    graph.add_edge("tools", "chatbot")
    
    workflow = graph.compile(checkpointer=checkpointer)

    # 6. Chat Loop
    print("MCP Chatbot initialized. Type 'quit' or 'close' to stop.")
    while True:
        user_input = input("Query: ")
        
        # Fixed: Added () to lower()
        if user_input.lower().strip() in ['quit', 'close']:
            print("Shutting down...")
            break
            
        if not user_input.strip():
            continue

        try:
            llm_output = await workflow.ainvoke(
                {"messages": [HumanMessage(user_input)]}, 
                config=config
            )
            
            # Print the final response (after any tool loops have finished)
            print(f"Response: {llm_output['messages'][-1].content}\n")
            
        except Exception as e:
            print(f"Error executing tools or LLM: {e}\n")


if __name__ == '__main__':
    asyncio.run(main())