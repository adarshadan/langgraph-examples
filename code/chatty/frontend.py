#import packages

import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph_chatbot_backend_with_persistence import workflow,generate_label,get_all_unique_threads,save_label
import uuid

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Utility Methods

def generate_thread_id():
    return str(uuid.uuid4())

def reset_chat():
    temp_thread_id = ''
    for thread_id, label in st.session_state.chat_threads.items():
        if label == '':
            temp_thread_id = thread_id
            break

    thread_id  = temp_thread_id or generate_thread_id()
    st.session_state.thread_id = thread_id
    add_thread(thread_id)
    st.session_state.message_history = []

def add_thread(thread_id):
    if thread_id not in st.session_state.chat_threads:
        st.session_state.chat_threads[thread_id]=''


def get_past_messages(thread_id):
    try:
        messages = workflow.get_state(config={'configurable':{'thread_id':thread_id}}).values['messages']
    except KeyError:
        messages  = [] #in case there are no messages typed in last session
    return messages

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Session Setup

if 'message_history' not in st.session_state:
    st.session_state.message_history = []

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = generate_thread_id()

if 'user_id' not in st.session_state:
    st.session_state.user_id = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state.chat_threads=get_all_unique_threads(st.session_state.user_id)

add_thread(st.session_state.thread_id)

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#UI page config, title, sidebar elements

st.set_page_config(page_title="Chatty", page_icon="💬")
st.title("💬 Chatty")
st.sidebar.title('Chatty - Your Personal AI Assistant')
if st.sidebar.button('➕ New Chat'):
    reset_chat()
st.sidebar.header('📝 Conversations')

for thread_id in reversed(st.session_state.chat_threads):

    label = st.session_state.chat_threads[thread_id] or '🚀 Current Conversation..'
    if st.sidebar.button(label,key=thread_id):
        st.session_state.thread_id = thread_id
        temp_messages = get_past_messages(thread_id)

        message_history =[]
        for message in temp_messages:
            if isinstance(message, HumanMessage):
               role = 'user'
            else:
               role = 'assistant'
            message_history.append({ 'role': role, 'content': message.content})
        st.session_state.message_history = message_history
            
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Display the past chat messages on the chat window

for msg in st.session_state.message_history:
    with st.chat_message(msg['role']):
        st.text(msg['content'])      
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Get user input and stream responses on the UI

config = {
    'configurable': {'thread_id': st.session_state.thread_id},
    'metadata': {'thread_id': st.session_state.thread_id},
    'run_name': 'chat_turn'
    }
user_message = st.chat_input('Type here....')
ai_message = ""

if user_message:
    with st.chat_message('user'):
        st.text(user_message)
    if not st.session_state.chat_threads[st.session_state.thread_id]:
        st.session_state.chat_threads[st.session_state.thread_id] = generate_label(user_message)
        save_label(st.session_state.thread_id, st.session_state.chat_threads[st.session_state.thread_id],st.session_state.user_id)

    with st.chat_message('assistant'):
        stream_object = workflow.stream({"messages": [HumanMessage(user_message)]},
                                        config=config,
                                        stream_mode='messages'
                                        )
        ai_message = st.write_stream( message_chunk.content for message_chunk, _ in stream_object)

    st.session_state.message_history.append({'role': 'user', 'content': user_message})
    st.session_state.message_history.append({'role': 'assistant', 'content': ai_message })
    st.rerun()