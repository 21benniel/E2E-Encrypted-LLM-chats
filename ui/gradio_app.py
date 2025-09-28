#!/usr/bin/env python3
"""
Gradio Web Interface for Encrypted LLM Chat

Alternative web interface using Gradio with:
- Clean chat interface
- Real-time encryption status
- Model configuration
- Performance metrics
"""

import gradio as gr
import time
import json
from datetime import datetime
from typing import List, Tuple, Dict, Any
import sys
sys.path.append('.')

try:
    from llm.encrypted_llm import EncryptedLLM
    from llm.model_manager import ModelManager
    from crypto.key_manager import KeyManager
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    print(f"Components not available: {e}")


class GradioEncryptedChat:
    """Gradio interface for encrypted LLM chat."""
    
    def __init__(self):
        """Initialize the Gradio chat interface."""
        self.encrypted_llm = None
        self.model_loaded = False
        self.chat_history = []
        self.stats = {
            'total_messages': 0,
            'total_generation_time': 0.0,
            'encryption_count': 0
        }
    
    def initialize_model(self, model_name: str, encryption_type: str) -> str:
        """Initialize the encrypted LLM model."""
        try:
            # Check certificates
            key_manager = KeyManager()
            key_type = encryption_type.lower().split('-')[0]
            
            try:
                key_manager.load_private_key(f"user_{key_type}_private_key.pem")
                key_manager.load_private_key(f"model_{key_type}_private_key.pem")
            except FileNotFoundError:
                return f"❌ Missing {key_type.upper()} certificates! Run: python crypto/generate_certs.py {'--ecc' if key_type == 'ecc' else ''}"
            
            # Initialize encrypted LLM
            self.encrypted_llm = EncryptedLLM(
                model_name=model_name,
                key_type=key_type
            )
            
            if self.encrypted_llm.initialize_model():
                self.model_loaded = True
                return f"✅ {model_name} initialized with {encryption_type} encryption!"
            else:
                return "❌ Failed to initialize model"
                
        except Exception as e:
            return f"❌ Initialization failed: {str(e)}"
    
    def chat_with_llm(
        self, 
        message: str, 
        history: List[List[str]], 
        max_length: int = 300,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Tuple[str, List[List[str]], str]:
        """Process a chat message through encrypted LLM."""
        
        if not self.encrypted_llm or not self.model_loaded:
            return "", history, "❌ Please initialize the model first!"
        
        if not message.strip():
            return "", history, "Please enter a message."
        
        try:
            # Show encryption status
            status = "🔐 Encrypting message..."
            
            # Encrypt the message
            start_time = time.time()
            encrypted_prompt = self.encrypted_llm.crypto.encrypt_message(
                message,
                self.encrypted_llm.model_public_key,
                {
                    "timestamp": datetime.now().isoformat(),
                    "user_id": "gradio_user",
                    "interface": "gradio"
                }
            )
            
            # Update status
            status = "🤖 AI is processing... (this may take a while)"
            
            # Process with encrypted LLM
            generation_params = {
                'max_length': max_length,
                'temperature': temperature,
                'top_p': top_p
            }
            
            encrypted_response = self.encrypted_llm.process_encrypted_prompt(
                encrypted_prompt,
                generation_params
            )
            
            # Decrypt response
            decrypted_response, response_metadata = self.encrypted_llm.crypto.decrypt_message(
                encrypted_response,
                self.encrypted_llm.user_private_key
            )
            
            # Update history - convert to messages format
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": decrypted_response})
            
            # Update statistics
            self.stats['total_messages'] += 1
            self.stats['total_generation_time'] += response_metadata.get('generation_time_seconds', 0)
            self.stats['encryption_count'] += 2  # encrypt + decrypt
            
            total_time = time.time() - start_time
            status = f"✅ Response generated in {total_time:.2f}s (Generation: {response_metadata.get('generation_time_seconds', 0):.2f}s)"
            
            return "", history, status
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            return "", history, error_msg
    
    def get_stats(self) -> str:
        """Get formatted statistics."""
        if self.stats['total_messages'] == 0:
            return "No messages yet"
        
        avg_time = self.stats['total_generation_time'] / self.stats['total_messages']
        
        return f"""
📊 **Session Statistics**
- Messages: {self.stats['total_messages']}
- Avg Generation Time: {avg_time:.2f}s  
- Encryptions: {self.stats['encryption_count']}
- Total Gen Time: {self.stats['total_generation_time']:.1f}s
        """
    
    def clear_chat(self) -> Tuple[List, str]:
        """Clear chat history."""
        self.chat_history = []
        return [], "Chat cleared"
    
    def export_chat(self, history: List) -> str:
        """Export chat history."""
        if not history:
            return "No chat history to export"
        
        try:
            export_data = {
                'export_time': datetime.now().isoformat(),
                'interface': 'gradio',
                'encryption_type': self.encrypted_llm.key_type if self.encrypted_llm else 'unknown',
                'model_name': self.encrypted_llm.model_name if self.encrypted_llm else 'unknown',
                'chat_history': history,
                'statistics': self.stats
            }
            
            filename = f"gradio_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return f"✅ Chat exported to {filename}"
            
        except Exception as e:
            return f"❌ Export failed: {str(e)}"
    
    def create_interface(self):
        """Create the Gradio interface."""
        
        # Custom CSS
        css = """
        .gradio-container {
            max-width: 1200px !important;
        }
        
        .chat-message {
            border-radius: 10px !important;
            margin: 5px 0 !important;
        }
        
        .encryption-status {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            padding: 10px !important;
            border-radius: 5px !important;
            margin: 10px 0 !important;
        }
        """
        
        with gr.Blocks(
            title="🔐 Encrypted LLM Chat", 
            theme=gr.themes.Soft(),
            css=css
        ) as demo:
            
            # Header
            gr.Markdown("""
            # 🔐 Encrypted LLM Chat
            
            **Secure AI conversations with end-to-end encryption**
            
            Your messages are encrypted before being sent to the AI, and responses are encrypted before being returned to you.
            Only you can decrypt the final responses using your private key.
            """)
            
            with gr.Row():
                with gr.Column(scale=3):
                    # Chat interface
                    chatbot = gr.Chatbot(
                        label="💬 Encrypted Chat",
                        height=400,
                        show_label=True,
                        container=True,
                        type="messages"
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="Type your message here... (it will be encrypted)",
                            label="Your message",
                            scale=4,
                            container=False
                        )
                        send_btn = gr.Button("Send 🔐", scale=1, variant="primary")
                    
                    # Status display
                    status_display = gr.Markdown("Ready to chat!", elem_classes=["encryption-status"])
                
                with gr.Column(scale=1):
                    # Configuration panel
                    gr.Markdown("### 🔧 Configuration")
                    
                    if COMPONENTS_AVAILABLE:
                        model_dropdown = gr.Dropdown(
                            choices=list(ModelManager.SUPPORTED_MODELS.keys()),
                            value="tinyllama",
                            label="🤖 AI Model",
                            info="Choose the AI model"
                        )
                        
                        encryption_dropdown = gr.Dropdown(
                            choices=["RSA-2048", "ECC-P256"],
                            value="RSA-2048",
                            label="🔐 Encryption",
                            info="Choose encryption type"
                        )
                        
                        init_btn = gr.Button("🚀 Initialize Model", variant="primary")
                        
                        # Advanced settings
                        with gr.Accordion("⚙️ Advanced Settings", open=False):
                            max_length_slider = gr.Slider(
                                minimum=50, maximum=1000, value=300, step=50,
                                label="Max Response Length"
                            )
                            temperature_slider = gr.Slider(
                                minimum=0.1, maximum=2.0, value=0.7, step=0.1,
                                label="Temperature"
                            )
                            top_p_slider = gr.Slider(
                                minimum=0.1, maximum=1.0, value=0.9, step=0.1,
                                label="Top-p"
                            )
                    
                    else:
                        gr.Markdown("❌ **Components not available**\n\nPlease check installation.")
                    
                    # Statistics
                    gr.Markdown("### 📊 Statistics")
                    stats_display = gr.Markdown("No statistics yet")
                    
                    # Controls
                    gr.Markdown("### 🛠️ Controls")
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary")
                    export_btn = gr.Button("📥 Export Chat")
                    
                    # Update stats button
                    refresh_stats_btn = gr.Button("🔄 Refresh Stats", size="sm")
            
            # Security info
            with gr.Accordion("🛡️ Security Information", open=False):
                gr.Markdown("""
                ### How Encryption Works:
                
                1. **Your message** is encrypted with the AI model's public key
                2. **AI model** decrypts your message with its private key
                3. **AI processes** your message and generates a response
                4. **AI encrypts** the response with your public key  
                5. **You decrypt** the response with your private key
                
                ### Security Features:
                - 🔐 **End-to-end encryption** using RSA-2048 or ECC-P256
                - 🔑 **Certificate-based authentication**
                - 🛡️ **No plaintext storage** or transmission
                - 🏠 **Local AI inference** for privacy
                - 🔒 **AES-256-GCM** for message content encryption
                
                ### Privacy Benefits:
                - Messages are never stored in plaintext
                - AI model runs locally on your machine
                - No data sent to external servers
                - You control your own encryption keys
                """)
            
            # Event handlers
            if COMPONENTS_AVAILABLE:
                # Initialize model
                init_btn.click(
                    fn=self.initialize_model,
                    inputs=[model_dropdown, encryption_dropdown],
                    outputs=[status_display]
                )
                
                # Send message
                def send_message(msg, history, max_len, temp, top_p):
                    return self.chat_with_llm(msg, history, max_len, temp, top_p)
                
                send_btn.click(
                    fn=send_message,
                    inputs=[msg_input, chatbot, max_length_slider, temperature_slider, top_p_slider],
                    outputs=[msg_input, chatbot, status_display]
                )
                
                # Enter key to send
                msg_input.submit(
                    fn=send_message,
                    inputs=[msg_input, chatbot, max_length_slider, temperature_slider, top_p_slider],
                    outputs=[msg_input, chatbot, status_display]
                )
            
            # Clear chat
            clear_btn.click(
                fn=self.clear_chat,
                inputs=[],
                outputs=[chatbot, status_display]
            )
            
            # Export chat
            export_btn.click(
                fn=self.export_chat,
                inputs=[chatbot],
                outputs=[status_display]
            )
            
            # Refresh stats
            refresh_stats_btn.click(
                fn=self.get_stats,
                inputs=[],
                outputs=[stats_display]
            )
        
        return demo


def main():
    """Main entry point for Gradio app."""
    if not COMPONENTS_AVAILABLE:
        print("❌ Required components not available. Please check your installation.")
        print("Make sure you have:")
        print("1. Generated certificates: python crypto/generate_certs.py")
        print("2. Installed requirements: pip install -r requirements.txt")
        print("3. Set PYTHONPATH: Run from project root directory")
        return
    
    # Create and launch the app
    chat_app = GradioEncryptedChat()
    demo = chat_app.create_interface()
    
    # Launch with custom settings
    demo.launch(
        server_name="0.0.0.0",  # Allow external access
        server_port=7860,
        share=False,  # Set to True to create public link
        show_error=True,
        inbrowser=True
    )


if __name__ == "__main__":
    main()
