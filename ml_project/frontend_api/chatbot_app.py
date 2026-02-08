import streamlit as st
import uuid
from ml_project.chatbot.langchain_ext.document_loader import get_openai_api_key
from ml_project.chatbot.langchain_ext.prompts import get_chat_prompt
from ml_project.chatbot.langchain_ext.memory import get_memory
from ml_project.chatbot.langchain_ext.chains import get_chat_chain


def initialize_chatbot():
    """Initialize the chatbot with API key, prompt, memory, and chain."""
    api_key = get_openai_api_key()
    prompt = get_chat_prompt("You are a helpful AI assistant.")
    memory = get_memory()
    chatbot = get_chat_chain(prompt, memory)
    return chatbot


def create_new_session():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())[:8]
    return {
        "id": session_id,
        "messages": [],
        "title": f"Chat {session_id}"
    }


def ai_chatbot_app():
    st.set_page_config(
        page_title="AI Chatbot",
        page_icon="🤖",
        layout="wide"
    )

    # Initialize session state
    if 'sessions' not in st.session_state:
        st.session_state.sessions = {}
        new_session = create_new_session()
        st.session_state.sessions[new_session['id']] = new_session
        st.session_state.current_session_id = new_session['id']
    
    if 'chatbot' not in st.session_state:
        with st.spinner("Initializing chatbot..."):
            st.session_state.chatbot = initialize_chatbot()
    
    # Get current session
    current_session = st.session_state.sessions[st.session_state.current_session_id]

    # Header with controls
    col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
    
    with col1:
        st.title("💬 AI Chatbot")
    
    with col2:
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            new_session = create_new_session()
            st.session_state.sessions[new_session['id']] = new_session
            st.session_state.current_session_id = new_session['id']
            st.session_state.chatbot = initialize_chatbot()  # Reset memory
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear", use_container_width=True, type="primary"):
            current_session['messages'] = []
            st.session_state.chatbot = initialize_chatbot()  # Reset memory
            st.rerun()
    
    with col4:
        # Session selector
        session_options = {
            sid: f"{s['title']} ({len(s['messages'])} msgs)" 
            for sid, s in st.session_state.sessions.items()
        }
        selected = st.selectbox(
            "Session",
            options=list(session_options.keys()),
            format_func=lambda x: session_options[x],
            index=list(session_options.keys()).index(st.session_state.current_session_id),
            label_visibility="collapsed"
        )
        if selected != st.session_state.current_session_id:
            st.session_state.current_session_id = selected
            st.rerun()
    

    st.divider()

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in current_session['messages']:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if user_input := st.chat_input("Type your message here..."):
        
        # Add user message to chat
        current_session['messages'].append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get AI response
        with st.chat_message("assistant"):
            try:
                response = st.session_state.chatbot.predict(input=user_input)
                st.markdown(response)
                
                # Add assistant message to chat
                current_session['messages'].append({
                    "role": "assistant",
                    "content": response
                })
                
                # Auto-update session title based on first message
                if len(current_session['messages']) == 2:
                    current_session['title'] = user_input[:30] + "..." if len(user_input) > 30 else user_input
                    
            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}"
                st.error(error_msg)
                current_session['messages'].append({
                    "role": "assistant",
                    "content": error_msg
                })


if __name__ == "__main__":
    ai_chatbot_app()