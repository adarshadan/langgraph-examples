#Workflow to implement a simple chatbot using langgraph and streamlit
#Package imports and load dot env
import os
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage,SystemMessage, HumanMessage
from langgraph.graph import add_messages
from langchain_groq import ChatGroq

from typing import Annotated, List,TypedDict
from dotenv import load_dotenv

load_dotenv()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Define the llm model for the chatbot

llm = ChatGroq(model=os.getenv('GROQ_MODEL'),
               api_key=os.getenv('GROQ_API_KEY'),
               temperature=0.2)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#class to define the state parameters 
class MessageState(TypedDict):

    messages : Annotated[List[BaseMessage], add_messages]

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Method to invoke the llm 

def chat_session(state:MessageState):

    SYSTEM_PROMPT = SystemMessage(content="You are Chatty, a helpful AI assistant. " \
    +"If ONLY asked who created or built you, say you were created by Adarsha Dan who is an Computer Science Engineer with 12+ years of IT experience in AI and Automation.")
    
    current_messages = [SYSTEM_PROMPT] + state['messages']

    response = llm.invoke(current_messages)

    return { 'messages': [response]}

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Method to generate label based on user conversation history

def generate_label(input_message:str) -> str:

    system_prompt = SystemMessage(content="Return ONLY the label text in 4-5 words. No quotes, no punctuation, no prefixes like 'Label:', no explanations." \
    "If the message is just a greeting or filler with no real topic, respond with [_NO_LABEL_] instead of a label.")

    user_prompt = HumanMessage(content=input_message)

    prompt = [system_prompt,user_prompt]

    response = llm.invoke(prompt).content.strip()

    return '' if '_no_label_' in response.lower() else response

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Define the State graph, nodes and edges
graph = StateGraph(MessageState)

graph.add_node('chat_session',chat_session)

graph.add_edge('__start__','chat_session')
graph.add_edge('chat_session','__end__')


#Setup the message in-memory save method on the workflow, build the graph and output to png file
checkpointer = InMemorySaver()

workflow = graph.compile(checkpointer=checkpointer)