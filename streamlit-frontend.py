import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

# only styling part here 
st.set_page_config(
    page_title="My AI Chatbot",
    page_icon="🤖"
)

# Simple styling
st.markdown("""
<style>
    .block-container {
        max-width: 750px;
        padding-top: 40px;
    }

    h1 {
        text-align: center;
    }

    .subtitle {
        text-align: center;
        color: gray;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)


st.title("🤖 My AI Chatbot")
st.markdown(
    "<p class='subtitle'>A simple chatbot built using LangGraph & Gemini</p>",
    unsafe_allow_html=True
)


# Main frontend for chatbot begins here: 

# st.session_state -> dict -> 
CONFIG = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

#{'role': 'user', 'content': 'Hi'}
#{'role': 'assistant', 'content': 'Hi=ello'}

user_input = st.chat_input('Type here')

if user_input:

    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]}, config=CONFIG)
    
    ai_message = response['messages'][-1].content
    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
    with st.chat_message('assistant'):
        st.text(ai_message)