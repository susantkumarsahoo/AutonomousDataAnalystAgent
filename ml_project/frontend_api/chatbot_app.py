import os
import sys
import time
import requests
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

import streamlit as st

from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url


logger = get_logger(__name__)


def ai_chatbot_app() -> None:
    """
    Advanced AI Chatbot Application with complete features
    - Session management
    - Chat history with persistence
    - File upload capabilities
    - Model configuration
    - Export chat history
    - Clear conversation
    - Token usage tracking
    """
    
    # ==================== CONFIGURATION ====================
    API_BASE_URL = os.getenv("CHATBOT_API_URL", "http://localhost:8000")
    
    # ==================== SESSION STATE INITIALIZATION ====================
    def initialize_session_state():
        """Initialize all session state variables"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'session_id' not in st.session_state:
            st.session_state.session_id = f"session_{int(time.time())}"
        
        if 'chatbot_initialized' not in st.session_state:
            st.session_state.chatbot_initialized = False
        
        if 'model_name' not in st.session_state:
            st.session_state.model_name = "gpt-4o-mini"
        
        if 'temperature' not in st.session_state:
            st.session_state.temperature = 0.7
        
        if 'max_tokens' not in st.session_state:
            st.session_state.max_tokens = 500
        
        if 'total_messages' not in st.session_state:
            st.session_state.total_messages = 0
        
        if 'conversation_started_at' not in st.session_state:
            st.session_state.conversation_started_at = None
    
    
    # ==================== API FUNCTIONS ====================
    def check_api_health() -> bool:
        """Check if the backend API is healthy"""
        try:
            response = requests.get(f"{fastapi_api_request_url}/chatbot_health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"API health check failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in health check: {str(e)}")
            return False
    
    
    def initialize_chatbot(session_id: str, model_name: str, temperature: float, max_tokens: int) -> bool:
        """Initialize chatbot session via API"""
        try:
            response = requests.post(
                f"{fastapi_api_request_url}/initialize",
                json={
                    "session_id": session_id,
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=10
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to initialize chatbot: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing chatbot: {str(e)}")
            return False
    
    
    def send_message(message: str, session_id: str, model_name: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Send message to chatbot and get response"""
        try:
            response = requests.post(
                f"{fastapi_api_request_url}/chat",
                json={
                    "message": message,
                    "session_id": session_id,
                    "model_name": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("response")
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.Timeout:
            logger.error("Request timeout while sending message")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending message: {str(e)}")
            return None
    
    
    def reset_conversation(session_id: str) -> bool:
        """Reset conversation memory"""
        try:
            response = requests.post(
                f"{fastapi_api_request_url}/reset",
                json={"session_id": session_id},
                timeout=10
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to reset conversation: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error resetting conversation: {str(e)}")
            return False
    
    
    # ==================== UTILITY FUNCTIONS ====================
    def export_chat_history() -> str:
        """Export chat history as JSON string"""
        export_data = {
            "session_id": st.session_state.session_id,
            "exported_at": datetime.now().isoformat(),
            "total_messages": st.session_state.total_messages,
            "conversation_started_at": st.session_state.conversation_started_at,
            "chat_history": st.session_state.chat_history
        }
        return json.dumps(export_data, indent=2)
    
    
    def save_message_to_history(role: str, content: str):
        """Save message to chat history"""
        st.session_state.chat_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        st.session_state.total_messages += 1
    
    
    def clear_chat_history():
        """Clear all chat history and reset conversation"""
        st.session_state.chat_history = []
        st.session_state.total_messages = 0
        st.session_state.conversation_started_at = None
        if reset_conversation(st.session_state.session_id):
            st.success("✅ Conversation cleared successfully!")
        else:
            st.warning("⚠️ Chat history cleared locally, but API reset failed")
    
    
    # ==================== MAIN APP LOGIC ====================
    try:
        # Initialize session state
        initialize_session_state()
        
        # Page configuration (must be first Streamlit command)
        st.set_page_config(
            page_title="AI Chatbot Assistant",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Page header
        st.title("🤖 AI Chatbot Assistant")
        st.markdown("---")
        
        # API Health Check
        with st.spinner("Checking API connection..."):
            api_healthy = check_api_health()
        
        if not api_healthy:
            st.error("❌ Backend API is not reachable. Please ensure the API server is running.")
            st.info(f"Expected API URL: {fastapi_api_request_url}")
            st.code("python ml_project/backend_api/chatbot_api.py", language="bash")
            return
        
        st.success("✅ Connected to backend API")
        
        # ==================== CONFIGURATION SECTION ====================
        with st.expander("⚙️ Configuration Settings", expanded=not st.session_state.chatbot_initialized):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                model_options = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
                current_index = model_options.index(st.session_state.model_name) if st.session_state.model_name in model_options else 0
                model_name = st.selectbox(
                    "Model",
                    options=model_options,
                    index=current_index,
                    help="Select the AI model to use"
                )
            
            with col2:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=float(st.session_state.temperature),
                    step=0.1,
                    help="Higher values make output more random, lower values more focused"
                )
            
            with col3:
                max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=50,
                    max_value=4000,
                    value=int(st.session_state.max_tokens),
                    step=50,
                    help="Maximum length of the response"
                )
            
            col_init, col_apply = st.columns(2)
            
            with col_init:
                if st.button("🚀 Initialize Chatbot", use_container_width=True):
                    with st.spinner("Initializing chatbot..."):
                        success = initialize_chatbot(
                            st.session_state.session_id,
                            model_name,
                            temperature,
                            max_tokens
                        )
                        
                        if success:
                            st.session_state.chatbot_initialized = True
                            st.session_state.model_name = model_name
                            st.session_state.temperature = temperature
                            st.session_state.max_tokens = max_tokens
                            st.session_state.conversation_started_at = datetime.now().isoformat()
                            st.success("✅ Chatbot initialized successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Failed to initialize chatbot")
            
            with col_apply:
                if st.button("🔄 Apply Changes", use_container_width=True):
                    st.session_state.model_name = model_name
                    st.session_state.temperature = temperature
                    st.session_state.max_tokens = max_tokens
                    st.info("✅ Configuration updated!")
        
        # ==================== STATISTICS SECTION ====================
        if st.session_state.chatbot_initialized:
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                st.metric("Total Messages", st.session_state.total_messages)
            
            with stat_col2:
                st.metric("Session ID", st.session_state.session_id.split('_')[-1])
            
            with stat_col3:
                st.metric("Model", st.session_state.model_name.replace("gpt-", ""))
            
            with stat_col4:
                st.metric("Temperature", f"{st.session_state.temperature:.1f}")
        
        st.markdown("---")
        
        # ==================== CHAT INTERFACE ====================
        if not st.session_state.chatbot_initialized:
            st.info("👆 Please initialize the chatbot using the configuration settings above")
            return
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            if len(st.session_state.chat_history) == 0:
                st.info("💬 Start a conversation by typing a message below!")
            else:
                for idx, message in enumerate(st.session_state.chat_history):
                    if message["role"] == "user":
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(message["content"])
                    else:
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(message["content"])
        
        # ==================== INPUT SECTION ====================
        st.markdown("---")
        
        # Chat input
        user_input = st.chat_input(
            "Type your message here...",
            key="chat_input"
        )
        
        # Process user input
        if user_input:
            if user_input.strip():
                # Save user message
                save_message_to_history("user", user_input)
                
                # Display user message immediately
                with st.chat_message("user", avatar="👤"):
                    st.markdown(user_input)
                
                # Get bot response
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Thinking..."):
                        response = send_message(
                            user_input,
                            st.session_state.session_id,
                            st.session_state.model_name,
                            st.session_state.temperature,
                            st.session_state.max_tokens
                        )
                    
                    if response:
                        st.markdown(response)
                        save_message_to_history("assistant", response)
                    else:
                        error_msg = "Sorry, I encountered an error. Please try again."
                        st.error(error_msg)
                        save_message_to_history("assistant", error_msg)
                
                # Rerun to update the interface
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("⚠️ Please enter a message")
        
        # ==================== ACTION BUTTONS ====================
        st.markdown("---")
        
        action_col1, action_col2, action_col3, action_col4 = st.columns(4)
        
        with action_col1:
            if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary"):
                clear_chat_history()
                time.sleep(0.5)
                st.rerun()
        
        with action_col2:
            if len(st.session_state.chat_history) > 0:
                export_data = export_chat_history()
                st.download_button(
                    label="📥 Export Chat",
                    data=export_data,
                    file_name=f"chat_history_{st.session_state.session_id}.json",
                    mime="application/json",
                    use_container_width=True
                )
            else:
                st.button("📥 Export Chat", use_container_width=True, disabled=True)
        
        with action_col3:
            if st.button("🔄 New Session", use_container_width=True):
                st.session_state.session_id = f"session_{int(time.time())}"
                st.session_state.chatbot_initialized = False
                clear_chat_history()
                st.success("✅ New session created!")
                time.sleep(0.5)
                st.rerun()
        
        with action_col4:
            if st.button("ℹ️ Help", use_container_width=True):
                st.info("""
                **How to use:**
                1. Configure model settings
                2. Click 'Initialize Chatbot'
                3. Start chatting!
                
                **Tips:**
                - Use higher temperature for creative responses
                - Use lower temperature for factual responses
                - Increase max tokens for longer responses
                """)
        
        # ==================== ADVANCED FEATURES ====================
        with st.expander("🔧 Advanced Features"):
            
            # File Upload Feature
            st.subheader("📎 Upload Context File")
            uploaded_file = st.file_uploader(
                "Upload a text file to provide context",
                type=['txt', 'md', 'json'],
                help="Upload a file to provide additional context to the chatbot"
            )
            
            if uploaded_file is not None:
                try:
                    file_content = uploaded_file.read().decode('utf-8')
                    preview_content = file_content[:500] + "..." if len(file_content) > 500 else file_content
                    st.text_area("File Content Preview", preview_content, height=150, disabled=True)
                    
                    if st.button("📤 Send File Content to Chat"):
                        prompt = f"I'm providing you with the following file content:\n\n```\n{file_content}\n```\n\nPlease analyze this and let me know if you have any questions."
                        
                        save_message_to_history("user", prompt)
                        
                        with st.spinner("Processing file..."):
                            response = send_message(
                                prompt,
                                st.session_state.session_id,
                                st.session_state.model_name,
                                st.session_state.temperature,
                                st.session_state.max_tokens
                            )
                        
                        if response:
                            save_message_to_history("assistant", response)
                            st.success("✅ File content sent to chatbot!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Failed to send file content")
                except UnicodeDecodeError:
                    st.error("❌ Unable to decode file. Please upload a valid text file.")
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
            
            st.markdown("---")
            
            # Quick Prompts
            st.subheader("⚡ Quick Prompts")
            quick_prompts = {
                "Explain like I'm 5": "Explain this in simple terms that a 5-year-old would understand",
                "Summarize": "Please summarize the above conversation",
                "Pros and Cons": "What are the pros and cons of what we discussed?",
                "Step by Step": "Break this down into step-by-step instructions",
                "Creative Ideas": "Give me 5 creative ideas related to our discussion"
            }
            
            prompt_cols = st.columns(len(quick_prompts))
            for idx, (label, prompt) in enumerate(quick_prompts.items()):
                with prompt_cols[idx]:
                    if st.button(label, use_container_width=True, key=f"quick_{idx}"):
                        save_message_to_history("user", prompt)
                        
                        with st.spinner("Processing..."):
                            response = send_message(
                                prompt,
                                st.session_state.session_id,
                                st.session_state.model_name,
                                st.session_state.temperature,
                                st.session_state.max_tokens
                            )
                        
                        if response:
                            save_message_to_history("assistant", response)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Failed to process quick prompt")
            
            st.markdown("---")
            
            # Conversation Summary
            st.subheader("📊 Conversation Insights")
            if len(st.session_state.chat_history) > 0:
                user_messages = [msg for msg in st.session_state.chat_history if msg["role"] == "user"]
                assistant_messages = [msg for msg in st.session_state.chat_history if msg["role"] == "assistant"]
                
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                
                with insight_col1:
                    st.metric("Your Messages", len(user_messages))
                
                with insight_col2:
                    st.metric("Bot Responses", len(assistant_messages))
                
                with insight_col3:
                    if st.session_state.conversation_started_at:
                        try:
                            start_time = datetime.fromisoformat(st.session_state.conversation_started_at)
                            duration = datetime.now() - start_time
                            st.metric("Duration", f"{duration.seconds // 60}m")
                        except Exception:
                            st.metric("Duration", "N/A")
            else:
                st.info("No conversation data available yet")
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray;'>"
            "Powered by OpenAI GPT Models | Built with Streamlit & FastAPI"
            "</div>",
            unsafe_allow_html=True
        )
    
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Error in chatbot app: {error_msg}")
        st.error(f"❌ An error occurred: {error_msg}")
        
        # Show detailed error in expander for debugging
        with st.expander("🐛 Error Details"):
            st.code(error_msg)
            st.info("Please check the logs for more information")


# Entry point for running as main module
if __name__ == "__main__":
    ai_chatbot_app()