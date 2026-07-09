import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph_chatbot_backend import workflow
import uuid


#Setup thread id as configurable for the graph invoke call
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
config = {'configurable': {'thread_id': st.session_state.thread_id}}

if 'message_history' not in st.session_state:
    st.session_state.message_history = []

for msg in st.session_state.message_history:
    with st.chat_message(msg['role']):
        st.text(msg['content'])
        print(f'Role: {msg['role']}, Message: {msg['content']}')

user_message = st.chat_input('Type here....')
if user_message:
    with st.chat_message('user'):
        st.text(user_message)

    with st.chat_message('assistant'):
        llm_response = workflow.invoke({"messages": [HumanMessage(user_message)]}, config=config)
        ai_message = llm_response['messages'][-1].content
        st.text(ai_message)

    st.session_state.message_history.append({'role': 'user', 'content': user_message})
    st.session_state.message_history.append({'role': 'assistant', 'content': ai_message})