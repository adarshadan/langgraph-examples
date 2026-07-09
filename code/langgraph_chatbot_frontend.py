import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph_chatbot_backend import workflow
import uuid

#Set the page title
st.set_page_config(page_title="Chatty", page_icon="💬")
st.title("💬 Chatty")

#Setup thread id as configurable for the graph invoke call
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
config = {'configurable': {'thread_id': st.session_state.thread_id}}

if 'message_history' not in st.session_state:
    st.session_state.message_history = []

for msg in st.session_state.message_history:
    with st.chat_message(msg['role']):
        st.text(msg['content'])
        print(f"Role: {msg['role']}, Message: {msg['content']}")


user_message = st.chat_input('Type here....')
ai_message = ""

if user_message:
    with st.chat_message('user'):
        st.text(user_message)

    with st.chat_message('assistant'):
        stream_object = workflow.stream({"messages": [HumanMessage(user_message)]},
                                        config=config,
                                        stream_mode='messages'
                                        )
        ai_message = st.write_stream( message_chunk.content for message_chunk, _ in stream_object)

    st.session_state.message_history.append({'role': 'user', 'content': user_message})
    st.session_state.message_history.append({'role': 'assistant', 'content': ai_message })