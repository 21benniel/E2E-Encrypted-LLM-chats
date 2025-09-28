#!/usr/bin/env python3
"""
Streamlit Web Interface for Encrypted LLM Chat

A beautiful, modern web interface that showcases:
- End-to-end encrypted AI conversations
- Real-time chat with local LLMs
- Encryption status visualization
- Model selection and configuration
- Chat history and export features
"""

import streamlit as st
import time
import json
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Import our encrypted LLM components
import sys
sys.path.append('.')

try:
    from llm.encrypted_llm import EncryptedLLM
    from llm.model_manager import ModelManager
    from crypto.key_manager import KeyManager
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    st.error(f"Components not available: {e}")


# Page configuration
st.set_page_config(
    page_title="🔐 Encrypted LLM Chat",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        margin-left: 2rem;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        margin-right: 2rem;
    }
    
    .encryption-badge {
        background: #28a745;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .metrics-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    
    .status-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 5px;
    }
    
    .status-online { background-color: #28a745; }
    .status-loading { background-color: #ffc107; }
    .status-offline { background-color: #dc3545; }
</style>
""", unsafe_allow_html=True)


class EncryptedChatUI:
    """Streamlit UI for Encrypted LLM Chat."""
    
    def __init__(self):
        """Initialize the chat UI."""
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Initialize Streamlit session state."""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'encrypted_llm' not in st.session_state:
            st.session_state.encrypted_llm = None
            
        if 'model_loaded' not in st.session_state:
            st.session_state.model_loaded = False
            
        if 'total_messages' not in st.session_state:
            st.session_state.total_messages = 0
            
        if 'total_generation_time' not in st.session_state:
            st.session_state.total_generation_time = 0.0
            
        if 'encryption_stats' not in st.session_state:
            st.session_state.encryption_stats = {
                'messages_encrypted': 0,
                'messages_decrypted': 0,
                'total_bundle_size': 0
            }
    
    def render_header(self):
        """Render the main header."""
        st.markdown("""
        <div class="main-header">
            <h1>🔐 Encrypted LLM Chat</h1>
            <p>Secure AI conversations with end-to-end encryption</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render the sidebar with controls and info."""
        with st.sidebar:
            st.header("🔧 Configuration")
            
            # Model selection
            if COMPONENTS_AVAILABLE:
                available_models = list(ModelManager.SUPPORTED_MODELS.keys())
                selected_model = st.selectbox(
                    "🤖 Select LLM Model",
                    available_models,
                    index=available_models.index("tinyllama") if "tinyllama" in available_models else 0,
                    help="Choose the AI model for conversations"
                )
                
                # Encryption type
                encryption_type = st.selectbox(
                    "🔐 Encryption Type",
                    ["RSA-2048", "ECC-P256"],
                    help="Choose encryption algorithm"
                )
                
                # Advanced settings
                with st.expander("⚙️ Advanced Settings"):
                    max_length = st.slider("Max Response Length", 50, 1000, 300)
                    temperature = st.slider("Temperature", 0.1, 2.0, 0.7, 0.1)
                    top_p = st.slider("Top-p", 0.1, 1.0, 0.9, 0.1)
                
                # Initialize button
                if st.button("🚀 Initialize Encrypted LLM", type="primary"):
                    self.initialize_encrypted_llm(selected_model, encryption_type.lower().split('-')[0])
                
                # Status indicator
                if st.session_state.encrypted_llm:
                    status = "🟢 Online" if st.session_state.model_loaded else "🟡 Loading"
                    st.success(f"Status: {status}")
                else:
                    st.error("Status: 🔴 Offline")
            
            st.divider()
            
            # Statistics
            st.header("📊 Session Stats")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Messages", st.session_state.total_messages)
                st.metric("Encrypted", st.session_state.encryption_stats['messages_encrypted'])
            
            with col2:
                avg_time = (st.session_state.total_generation_time / max(st.session_state.total_messages, 1))
                st.metric("Avg Time", f"{avg_time:.1f}s")
                st.metric("Decrypted", st.session_state.encryption_stats['messages_decrypted'])
            
            # Security info
            st.header("🛡️ Security Info")
            st.info("""
            **🔐 End-to-End Encryption**
            - Messages encrypted with recipient's public key
            - Only you can decrypt responses
            - No plaintext stored or transmitted
            - Certificate-based authentication
            """)
            
            # Export chat
            if st.session_state.chat_history:
                if st.button("📥 Export Chat History"):
                    self.export_chat_history()
            
            # Clear chat
            if st.button("🗑️ Clear Chat", type="secondary"):
                st.session_state.chat_history = []
                st.rerun()
    
    def initialize_encrypted_llm(self, model_name: str, encryption_type: str):
        """Initialize the encrypted LLM with selected parameters."""
        try:
            with st.spinner(f"Initializing {model_name} with {encryption_type.upper()} encryption..."):
                # Check if certificates exist
                key_manager = KeyManager()
                try:
                    key_manager.load_private_key(f"user_{encryption_type}_private_key.pem")
                    key_manager.load_private_key(f"model_{encryption_type}_private_key.pem")
                except FileNotFoundError:
                    st.error(f"""
                    ❌ Missing {encryption_type.upper()} certificates!
                    
                    Please run: `python crypto/generate_certs.py {"--ecc" if encryption_type == "ecc" else ""}`
                    """)
                    return
                
                # Initialize encrypted LLM
                encrypted_llm = EncryptedLLM(
                    model_name=model_name,
                    key_type=encryption_type
                )
                
                # Load the model
                if encrypted_llm.initialize_model():
                    st.session_state.encrypted_llm = encrypted_llm
                    st.session_state.model_loaded = True
                    st.success(f"✅ {model_name} initialized with {encryption_type.upper()} encryption!")
                else:
                    st.error("❌ Failed to initialize model")
                    
        except Exception as e:
            st.error(f"❌ Initialization failed: {str(e)}")
    
    def render_chat_interface(self):
        """Render the main chat interface."""
        st.header("💬 Encrypted Chat")
        
        # Chat history
        chat_container = st.container()
        
        with chat_container:
            if st.session_state.chat_history:
                for i, message in enumerate(st.session_state.chat_history):
                    self.render_message(message, i)
            else:
                st.info("👋 Start a conversation! Your messages will be encrypted end-to-end.")
        
        # Chat input
        st.divider()
        
        # Input form
        with st.form("chat_form", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input(
                    "Your message:",
                    placeholder="Type your message here... (it will be encrypted)",
                    label_visibility="collapsed"
                )
            
            with col2:
                send_button = st.form_submit_button("Send 🔐", type="primary")
            
            if send_button and user_input.strip():
                if st.session_state.encrypted_llm and st.session_state.model_loaded:
                    self.process_user_message(user_input.strip())
                else:
                    st.error("Please initialize the encrypted LLM first!")
    
    def render_message(self, message: Dict[str, Any], index: int):
        """Render a single chat message."""
        timestamp = message.get('timestamp', 'Unknown time')
        
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="user-message">
                <strong>👤 You</strong> <span class="encryption-badge">🔐 ENCRYPTED</span>
                <small style="float: right;">{timestamp}</small><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Show encryption details in expander
            if 'encryption_info' in message:
                with st.expander(f"🔍 Encryption Details - Message {index + 1}"):
                    info = message['encryption_info']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Bundle Size", f"{info.get('bundle_size', 0)} chars")
                    with col2:
                        st.metric("Encryption Time", f"{info.get('encryption_time', 0):.3f}s")
                    with col3:
                        st.metric("Algorithm", info.get('algorithm', 'Unknown'))
        
        else:  # assistant
            st.markdown(f"""
            <div class="assistant-message">
                <strong>🤖 AI Assistant</strong> <span class="encryption-badge">🔐 ENCRYPTED</span>
                <small style="float: right;">{timestamp}</small><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
            
            # Show generation details
            if 'generation_info' in message:
                with st.expander(f"⚡ Generation Details - Response {index + 1}"):
                    info = message['generation_info']
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Generation Time", f"{info.get('generation_time', 0):.2f}s")
                    with col2:
                        st.metric("Response Length", f"{info.get('response_length', 0)} chars")
                    with col3:
                        st.metric("Model", info.get('model_name', 'Unknown'))
                    with col4:
                        st.metric("Temperature", info.get('temperature', 'N/A'))
    
    def process_user_message(self, user_input: str):
        """Process a user message through the encrypted LLM."""
        start_time = time.time()
        
        # Add user message to history
        user_message = {
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'encryption_info': {}
        }
        
        # Show processing status
        with st.spinner("🔐 Encrypting message..."):
            try:
                # Encrypt the prompt
                encrypt_start = time.time()
                encrypted_prompt = st.session_state.encrypted_llm.crypto.encrypt_message(
                    user_input,
                    st.session_state.encrypted_llm.model_public_key,
                    {
                        "timestamp": datetime.now().isoformat(),
                        "user_id": "streamlit_user",
                        "session_id": "web_session"
                    }
                )
                encrypt_time = time.time() - encrypt_start
                
                # Update user message with encryption info
                user_message['encryption_info'] = {
                    'bundle_size': len(encrypted_prompt),
                    'encryption_time': encrypt_time,
                    'algorithm': st.session_state.encrypted_llm.key_type.upper()
                }
                
                st.session_state.chat_history.append(user_message)
                st.session_state.encryption_stats['messages_encrypted'] += 1
                st.session_state.encryption_stats['total_bundle_size'] += len(encrypted_prompt)
                
            except Exception as e:
                st.error(f"Encryption failed: {e}")
                return
        
        # Process with encrypted LLM
        with st.spinner("🤖 AI is thinking... (this may take a while)"):
            try:
                # Get generation parameters from sidebar
                generation_params = {
                    'max_length': st.session_state.get('max_length', 300),
                    'temperature': st.session_state.get('temperature', 0.7),
                    'top_p': st.session_state.get('top_p', 0.9)
                }
                
                # Process encrypted prompt
                encrypted_response = st.session_state.encrypted_llm.process_encrypted_prompt(
                    encrypted_prompt,
                    generation_params
                )
                
                # Decrypt response
                decrypted_response, response_metadata = st.session_state.encrypted_llm.crypto.decrypt_message(
                    encrypted_response,
                    st.session_state.encrypted_llm.user_private_key
                )
                
                # Add assistant message to history
                assistant_message = {
                    'role': 'assistant',
                    'content': decrypted_response,
                    'timestamp': datetime.now().strftime("%H:%M:%S"),
                    'generation_info': {
                        'generation_time': response_metadata.get('generation_time_seconds', 0),
                        'response_length': len(decrypted_response),
                        'model_name': response_metadata.get('model_name', 'Unknown'),
                        'temperature': generation_params.get('temperature', 0.7)
                    }
                }
                
                st.session_state.chat_history.append(assistant_message)
                
                # Update statistics
                st.session_state.total_messages += 1
                st.session_state.total_generation_time += response_metadata.get('generation_time_seconds', 0)
                st.session_state.encryption_stats['messages_decrypted'] += 1
                
            except Exception as e:
                st.error(f"AI processing failed: {e}")
                # Remove the user message if processing failed
                if st.session_state.chat_history and st.session_state.chat_history[-1]['role'] == 'user':
                    st.session_state.chat_history.pop()
        
        # Rerun to show new messages
        st.rerun()
    
    def export_chat_history(self):
        """Export chat history as JSON."""
        try:
            chat_data = {
                'export_time': datetime.now().isoformat(),
                'total_messages': len(st.session_state.chat_history),
                'encryption_type': st.session_state.encrypted_llm.key_type if st.session_state.encrypted_llm else 'Unknown',
                'chat_history': st.session_state.chat_history,
                'statistics': {
                    'total_messages': st.session_state.total_messages,
                    'total_generation_time': st.session_state.total_generation_time,
                    'encryption_stats': st.session_state.encryption_stats
                }
            }
            
            json_str = json.dumps(chat_data, indent=2)
            
            st.download_button(
                label="💾 Download Chat History",
                data=json_str,
                file_name=f"encrypted_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"Export failed: {e}")
    
    def render_encryption_demo(self):
        """Render a demo section showing encryption in action."""
        st.header("🔍 Encryption Demo")
        
        demo_text = st.text_input("Enter text to see encryption:", "Hello, encrypted world!")
        
        if demo_text and st.session_state.encrypted_llm:
            try:
                # Show encryption process
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📝 Original Text")
                    st.code(demo_text)
                    st.caption(f"Length: {len(demo_text)} characters")
                
                with col2:
                    encrypted = st.session_state.encrypted_llm.crypto.encrypt_message(
                        demo_text,
                        st.session_state.encrypted_llm.model_public_key,
                        {"demo": True}
                    )
                    
                    st.subheader("🔐 Encrypted Bundle")
                    st.code(encrypted[:200] + "..." if len(encrypted) > 200 else encrypted)
                    st.caption(f"Length: {len(encrypted)} characters")
                
                # Show decryption
                st.subheader("🔓 Decryption Process")
                decrypted, metadata = st.session_state.encrypted_llm.crypto.decrypt_message(
                    encrypted,
                    st.session_state.encrypted_llm.model_private_key
                )
                
                if decrypted == demo_text:
                    st.success("✅ Decryption successful! Text matches original.")
                else:
                    st.error("❌ Decryption failed!")
                
            except Exception as e:
                st.error(f"Demo failed: {e}")
    
    def run(self):
        """Run the Streamlit app."""
        if not COMPONENTS_AVAILABLE:
            st.error("❌ Required components not available. Please check your installation.")
            st.info("""
            Make sure you have:
            1. Generated certificates: `python crypto/generate_certs.py`
            2. Installed requirements: `pip install -r requirements.txt`
            3. Set PYTHONPATH: Run from project root directory
            """)
            return
        
        self.render_header()
        
        # Main layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self.render_chat_interface()
        
        with col2:
            self.render_sidebar()
        
        # Additional sections
        st.divider()
        
        tabs = st.tabs(["🔍 Encryption Demo", "📊 Analytics", "ℹ️ About"])
        
        with tabs[0]:
            self.render_encryption_demo()
        
        with tabs[1]:
            self.render_analytics()
        
        with tabs[2]:
            self.render_about()
    
    def render_analytics(self):
        """Render analytics and performance charts."""
        st.header("📊 Performance Analytics")
        
        if st.session_state.chat_history:
            # Extract generation times
            generation_times = []
            message_lengths = []
            
            for msg in st.session_state.chat_history:
                if msg['role'] == 'assistant' and 'generation_info' in msg:
                    generation_times.append(msg['generation_info'].get('generation_time', 0))
                    message_lengths.append(msg['generation_info'].get('response_length', 0))
            
            if generation_times:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Generation time chart
                    fig_time = px.line(
                        x=list(range(1, len(generation_times) + 1)),
                        y=generation_times,
                        title="AI Response Generation Time",
                        labels={'x': 'Message Number', 'y': 'Time (seconds)'}
                    )
                    st.plotly_chart(fig_time, use_container_width=True)
                
                with col2:
                    # Response length chart
                    fig_length = px.bar(
                        x=list(range(1, len(message_lengths) + 1)),
                        y=message_lengths,
                        title="AI Response Length",
                        labels={'x': 'Message Number', 'y': 'Characters'}
                    )
                    st.plotly_chart(fig_length, use_container_width=True)
                
                # Summary statistics
                st.subheader("📈 Summary Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Avg Generation Time", f"{sum(generation_times)/len(generation_times):.2f}s")
                with col2:
                    st.metric("Fastest Response", f"{min(generation_times):.2f}s")
                with col3:
                    st.metric("Slowest Response", f"{max(generation_times):.2f}s")
                with col4:
                    st.metric("Avg Response Length", f"{sum(message_lengths)//len(message_lengths)} chars")
        else:
            st.info("Start chatting to see analytics!")
    
    def render_about(self):
        """Render about section."""
        st.header("ℹ️ About Encrypted LLM Chat")
        
        st.markdown("""
        ### 🔐 What is this?
        
        This is a **proof-of-concept** encrypted AI chat application that demonstrates:
        
        - **End-to-end encryption** of AI conversations
        - **Local AI inference** for privacy
        - **Certificate-based security** 
        - **Modern web interface** with real-time chat
        
        ### 🛡️ Security Features
        
        - **RSA-2048** or **ECC-P256** encryption
        - **AES-256-GCM** for message content
        - **Self-signed certificates** for identity
        - **No plaintext storage** or transmission
        
        ### 🤖 Supported Models
        
        - **TinyLlama 1.1B** - Ultra lightweight
        - **Phi-3 Mini 3.8B** - Fast and efficient  
        - **Mistral 7B** - High quality responses
        - **Custom models** via Hugging Face
        
        ### 🚀 Technical Stack
        
        - **Frontend**: Streamlit + Plotly
        - **Backend**: Python + Transformers
        - **Crypto**: Python cryptography library
        - **AI**: Local LLM inference
        
        ### 📝 Use Cases
        
        - **Privacy-focused AI** conversations
        - **Sensitive data** processing
        - **Educational** cryptography demos
        - **Research** into encrypted AI systems
        
        ---
        
        **⚠️ Note**: This is a demonstration project. For production use, additional security measures would be recommended.
        """)


def main():
    """Main entry point for Streamlit app."""
    app = EncryptedChatUI()
    app.run()


if __name__ == "__main__":
    main()
