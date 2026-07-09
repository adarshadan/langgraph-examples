#Workflow to implement a simple chatbot using langgraph and streamlit
#Package imports and load dot env
import os


from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage,HumanMessage
from langgraph.graph import add_messages
from langchain_groq import ChatGroq

from typing import Annotated, List,TypedDict
from dotenv import load_dotenv

load_dotenv()


#Define the llm model for the chatbot
llm = ChatGroq(model=os.getenv('GROQ_MODEL'),
               api_key=os.getenv('GROQ_API_KEY'),
               temperature=0.2)


#class to define the state parameters 
class MessageState(TypedDict):

    messages : Annotated[List[BaseMessage], add_messages]


#Method to invoke the llm 
def chat_session(state:MessageState):

    current_messages = state['messages']

    response = llm.invoke(current_messages)

    return { 'messages': [response]}


#Define the State graph, nodes and edges
graph = StateGraph(MessageState)

graph.add_node('chat_session',chat_session)

graph.add_edge('__start__','chat_session')
graph.add_edge('chat_session','__end__')


#Setup the message in-memory save method on the workflow, build the graph and output to png file
checkpointer = InMemorySaver()

workflow = graph.compile(checkpointer=checkpointer)