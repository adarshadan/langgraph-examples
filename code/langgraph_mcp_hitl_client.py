import os,sys
import asyncio
from typing import Annotated, List, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, BaseMessage, ToolMessage

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()


class ChatState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


async def main():
    llm = ChatGroq(model=os.getenv('GROQ_MODEL'), api_key=os.getenv('GROQ_API_KEY'))
    config = {'configurable': {'thread_id': 1}}

    math_server_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "langgraph_mcp_math_server.py"
    )

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

    tools = await client.get_tools()
    tools_by_name = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    async def chatbot(state: ChatState):
        response = await llm_with_tools.ainvoke(state['messages'])
        return {"messages": [response]}

    async def human_approval_tool_node(state: ChatState):
        last_message = state["messages"][-1]
        outputs = []
        for tc in last_message.tool_calls:
            decision = interrupt({
                "question": f"Approve call to '{tc['name']}' with args {tc['args']}? (yes/no)"
            })
            if decision:
                tool = tools_by_name[tc["name"]]
                result = await tool.ainvoke(tc["args"])
            else:
                result = "Tool usage rejected by user, unable to provide information!"
            outputs.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"], name=tc["name"])
            )
        return {"messages": outputs}

    checkpointer = InMemorySaver()
    graph = StateGraph(ChatState)
    graph.add_node("chatbot", chatbot)
    graph.add_node("tools", human_approval_tool_node)
    graph.add_edge(START, "chatbot")
    graph.add_conditional_edges("chatbot", tools_condition)
    graph.add_edge("tools", "chatbot")
    workflow = graph.compile(checkpointer=checkpointer)

    async def run_turn(initial_input):
        result = await workflow.ainvoke(initial_input, config=config)
        while "__interrupt__" in result:
            info = result["__interrupt__"][0]
            question = info.value.get("question", "Approve? (yes/no)")
            ans = input(f"{question} ").strip().lower()
            decision = ans in ("y", "yes")
            result = await workflow.ainvoke(Command(resume=decision), config=config)
        return result

    print("MCP Chatbot initialized. Type 'quit' or 'close' to stop.")
    while True:
        user_input = input("Query: ")
        if user_input.lower().strip() in ['quit', 'close']:
            print("Shutting down...")
            break
        if not user_input.strip():
            continue

        try:
            llm_output = await run_turn({"messages": [HumanMessage(user_input)]})
            print(f"Response: {llm_output['messages'][-1].content}\n")
        except Exception as e:
            print(f"Error executing tools or LLM: {e}\n")


if __name__ == '__main__':
    asyncio.run(main())