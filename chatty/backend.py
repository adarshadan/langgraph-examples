#Workflow to implement a simple chatbot using langgraph and streamlit
#Package imports and load dot env
import os
import sqlite3
import time
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langgraph.graph import add_messages
from langchain_groq import ChatGroq

from typing import Annotated
from typing import List
from typing import TypedDict
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
# Get all the unique threads

def get_all_unique_threads(user_id:str):

    cursor = conn.execute('SELECT thread_id, label from thread_label_mapping WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()

    label_map = {thread_id:label for thread_id,label in rows}

    all_threads = {}
    for checkpoint in checkpointer.list(None):
        chk_thread_id = checkpoint.config['configurable']['thread_id']

        if chk_thread_id in label_map:
            all_threads[chk_thread_id] = label_map.get(chk_thread_id,'')

    return all_threads
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Method to insert the thread_id,label mapping into the SQLite db table

def save_label(thread_id:str, label:str,user_id:str):

    conn.execute('''INSERT INTO thread_label_mapping
                 VALUES(?,?,?)
                 ON CONFLICT(thread_id) 
                 DO UPDATE 
                 SET label = excluded.label''',(thread_id,label,user_id))
    conn.commit()
 
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Define the State graph, nodes and edges

graph = StateGraph(MessageState)

graph.add_node('chat_session',chat_session)

graph.add_edge('__start__','chat_session')
graph.add_edge('chat_session','__end__')

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Setup the SQLite db, checkpointer and compile the graph and generate the workflow graph object

conn = sqlite3.connect(database='./chatbot.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)
conn.execute('''CREATE TABLE IF NOT EXISTS thread_label_mapping
             (thread_id TEXT PRIMARY KEY,
             label TEXT,
             user_id TEXT) ''')
conn.commit()

workflow = graph.compile(checkpointer=checkpointer)
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Logic to test the backend implementation

if __name__ == '__main__':

    thread_id = 1
    config = { 'configurable':{'thread_id': thread_id}}

    stream_object = workflow.stream({'messages': [HumanMessage('How many inches in a feet?')]}, config=config, stream_mode='messages')

    for message_chunk , metadata in stream_object:
        
        for char in message_chunk.content:
            print(char, end='', flush=True) # No space between characters
            time.sleep(0.01) # Shorter delay for characters