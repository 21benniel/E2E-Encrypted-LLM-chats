"""
Encrypted LLM Wrapper

Integrates the LLM with the encryption system to provide secure AI inference.
This is the core component that combines crypto and LLM functionality.
"""

import time
import json
from typing import Dict, Any, Optional, Tuple, List

from crypto.key_manager import KeyManager
from crypto.message_crypto import MessageCrypto
from crypto.conversation_memory import EncryptedConversationMemory
from llm.model_manager import ModelManager


class EncryptedLLM:
    """
    Encrypted LLM wrapper that handles the complete flow:
    1. Receive encrypted prompt
    2. Decrypt prompt with model's private key
    3. Generate LLM response
    4. Encrypt response with user's public key
    5. Return encrypted response
    """
    
    def __init__(
        self,
        model_name: str = "phi-3-mini",
        key_type: str = "rsa",
        certs_dir: str = "certs",
        enable_memory: bool = True,
        memory_storage_dir: str = "conversations"
    ):
        """
        Initialize EncryptedLLM.
        
        Args:
            model_name: LLM model to use
            key_type: Encryption type ("rsa" or "ecc")
            certs_dir: Directory containing certificates
            enable_memory: Enable persistent conversation memory
            memory_storage_dir: Directory for conversation storage
        """
        self.model_name = model_name
        self.key_type = key_type
        self.enable_memory = enable_memory
        
        # Initialize components
        self.key_manager = KeyManager(certs_dir)
        self.crypto = MessageCrypto()
        self.model_manager = ModelManager(model_name)
        
        # Initialize memory system if enabled
        if self.enable_memory:
            try:
                user_key_file = f"{certs_dir}/user_{key_type}_private_key.pem"
                self.memory = EncryptedConversationMemory(
                    storage_dir=memory_storage_dir,
                    user_key_file=user_key_file
                )
                print("✅ Encrypted conversation memory enabled")
            except Exception as e:
                print(f"⚠️  Failed to initialize memory: {e}")
                self.memory = None
                self.enable_memory = False
        else:
            self.memory = None
        
        # Load keys
        self._load_keys()
        
        # Model loading status
        self.model_loaded = False
    
    def _load_keys(self):
        """Load model and user keys for encryption/decryption."""
        try:
            # Model keys (for decrypting incoming prompts)
            self.model_private_key = self.key_manager.load_private_key(
                f"model_{self.key_type}_private_key.pem"
            )
            self.model_public_key = self.key_manager.load_public_key(
                f"model_{self.key_type}_public_key.pem"
            )
            
            # User keys (for encrypting responses)
            self.user_private_key = self.key_manager.load_private_key(
                f"user_{self.key_type}_private_key.pem"
            )
            self.user_public_key = self.key_manager.load_public_key(
                f"user_{self.key_type}_public_key.pem"
            )
            
            print(f"✅ Loaded {self.key_type.upper()} keys for encrypted LLM")
            
        except FileNotFoundError as e:
            print(f"❌ Error loading keys: {e}")
            print(f"   Run 'python crypto/generate_certs.py --{'ecc' if self.key_type == 'ecc' else ''}' to generate keys")
            raise
    
    def initialize_model(self) -> bool:
        """Initialize the LLM model."""
        if self.model_loaded:
            return True
        
        print(f"🔄 Initializing {self.model_name} for encrypted inference...")
        
        if self.model_manager.load_model():
            self.model_loaded = True
            print(f"✅ Encrypted LLM ready with {self.model_name}")
            return True
        else:
            print(f"❌ Failed to load {self.model_name}")
            return False
    
    def process_encrypted_prompt(
        self,
        encrypted_bundle: str,
        generation_params: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        use_context: bool = True
    ) -> str:
        """
        Process an encrypted prompt and return encrypted response.
        
        This is the main method that implements the secure LLM flow:
        1. Decrypt incoming prompt
        2. Load conversation context if available
        3. Generate LLM response with context
        4. Save to conversation memory
        5. Encrypt response for user
        
        Args:
            encrypted_bundle: Encrypted prompt from user
            generation_params: Optional parameters for text generation
            conversation_id: Optional conversation ID for memory
            use_context: Whether to use conversation context
            
        Returns:
            Encrypted response bundle for user
        """
        if not self.model_loaded:
            if not self.initialize_model():
                error_response = "❌ Model not available"
                return self._encrypt_response_for_user(error_response, {"error": "model_not_loaded"})
        
        try:
            # Step 1: Decrypt the incoming prompt
            print("🔓 Decrypting incoming prompt...")
            decrypted_prompt, metadata = self.crypto.decrypt_message(
                encrypted_bundle,
                self.model_private_key
            )
            
            print(f"   📝 Decrypted prompt: {decrypted_prompt}")
            print(f"   📋 Metadata: {json.dumps(metadata, indent=2)}")
            
            # Step 2: Handle conversation memory
            conversation_context = ""
            if self.enable_memory and conversation_id and use_context:
                try:
                    conversation_context = self.memory.get_conversation_context(
                        conversation_id, 
                        max_messages=10, 
                        max_tokens=1500
                    )
                    if conversation_context:
                        print(f"   🧠 Loaded conversation context ({len(conversation_context)} chars)")
                except Exception as e:
                    print(f"   ⚠️  Failed to load context: {e}")
            
            # Step 3: Build enhanced prompt with context
            if conversation_context:
                enhanced_prompt = f"""Previous conversation:
{conversation_context}

Current message:
Human: {decrypted_prompt}
Assistant:"""
            else:
                enhanced_prompt = decrypted_prompt
            
            # Step 4: Generate LLM response
            print("🧠 Generating LLM response...")
            start_time = time.time()
            
            # Set default generation parameters
            gen_params = generation_params or {}
            default_params = {
                "max_length": 512,
                "temperature": 0.7,
                "top_p": 0.9,
                "do_sample": True
            }
            default_params.update(gen_params)
            
            llm_response = self.model_manager.generate_response(
                enhanced_prompt,
                **default_params
            )
            
            generation_time = time.time() - start_time
            print(f"   🤖 Generated response: {llm_response}")
            print(f"   ⏱️  Generation time: {generation_time:.2f}s")
            
            # Step 5: Save to conversation memory
            if self.enable_memory and conversation_id:
                try:
                    # Save user message
                    self.memory.add_message(
                        conversation_id, 
                        "user", 
                        decrypted_prompt, 
                        metadata
                    )
                    
                    # Save assistant response
                    response_metadata = {
                        "generation_time_seconds": round(generation_time, 2),
                        "model_name": self.model_name,
                        "generation_params": default_params,
                        "context_used": bool(conversation_context)
                    }
                    
                    self.memory.add_message(
                        conversation_id, 
                        "assistant", 
                        llm_response, 
                        response_metadata
                    )
                    
                    print(f"   💾 Saved to conversation: {conversation_id}")
                    
                except Exception as e:
                    print(f"   ⚠️  Failed to save to memory: {e}")
            
            # Step 6: Encrypt response for user
            print("🔐 Encrypting response for user...")
            response_metadata = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "model_name": self.model_name,
                "generation_time_seconds": round(generation_time, 2),
                "original_prompt_hash": hash(decrypted_prompt) % 10000,
                "response_length": len(llm_response),
                "generation_params": default_params,
                "conversation_id": conversation_id,
                "context_used": bool(conversation_context)
            }
            
            encrypted_response = self._encrypt_response_for_user(llm_response, response_metadata)
            
            print(f"   🔐 Encrypted response size: {len(encrypted_response)} characters")
            
            return encrypted_response
            
        except Exception as e:
            print(f"❌ Error processing encrypted prompt: {e}")
            error_response = f"❌ Error: {str(e)}"
            error_metadata = {
                "error": True,
                "error_type": type(e).__name__,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "conversation_id": conversation_id
            }
            return self._encrypt_response_for_user(error_response, error_metadata)
    
    def _encrypt_response_for_user(self, response: str, metadata: Dict[str, Any]) -> str:
        """Encrypt a response for the user."""
        return self.crypto.encrypt_message(
            response,
            self.user_public_key,
            metadata
        )
    
    # Conversation Management Methods
    
    def create_conversation(self, title: str = None, tags: List[str] = None) -> Optional[str]:
        """Create a new conversation and return its ID."""
        if not self.enable_memory:
            print("⚠️  Memory is disabled. Cannot create conversation.")
            return None
        
        try:
            return self.memory.create_conversation(
                title=title,
                model_name=self.model_name,
                encryption_type=self.key_type,
                tags=tags
            )
        except Exception as e:
            print(f"❌ Failed to create conversation: {e}")
            return None
    
    def list_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent conversations."""
        if not self.enable_memory:
            return []
        
        try:
            conversations = self.memory.list_conversations(limit)
            return [
                {
                    "id": conv.conversation_id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "last_updated": conv.last_updated,
                    "message_count": conv.message_count,
                    "model_name": conv.model_name,
                    "tags": conv.tags
                }
                for conv in conversations
            ]
        except Exception as e:
            print(f"❌ Failed to list conversations: {e}")
            return []
    
    def get_conversation_history(self, conversation_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get conversation history in a format suitable for UI."""
        if not self.enable_memory:
            return []
        
        try:
            messages = self.memory.get_conversation_messages(conversation_id, limit)
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in messages
            ]
        except Exception as e:
            print(f"❌ Failed to get conversation history: {e}")
            return []
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        if not self.enable_memory:
            return False
        
        try:
            return self.memory.delete_conversation(conversation_id)
        except Exception as e:
            print(f"❌ Failed to delete conversation: {e}")
            return False
    
    def search_conversations(self, query: str) -> List[Dict[str, Any]]:
        """Search conversations."""
        if not self.enable_memory:
            return []
        
        try:
            conversations = self.memory.search_conversations(query)
            return [
                {
                    "id": conv.conversation_id,
                    "title": conv.title,
                    "created_at": conv.created_at,
                    "message_count": conv.message_count,
                    "tags": conv.tags
                }
                for conv in conversations
            ]
        except Exception as e:
            print(f"❌ Failed to search conversations: {e}")
            return []
    
    def export_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Export a conversation."""
        if not self.enable_memory:
            return None
        
        try:
            return self.memory.export_conversation(conversation_id)
        except Exception as e:
            print(f"❌ Failed to export conversation: {e}")
            return None
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        if not self.enable_memory:
            return {"memory_enabled": False}
        
        try:
            stats = self.memory.get_storage_stats()
            stats["memory_enabled"] = True
            return stats
        except Exception as e:
            print(f"❌ Failed to get memory stats: {e}")
            return {"memory_enabled": True, "error": str(e)}
    
    def chat_session(self):
        """Run an interactive encrypted chat session."""
        print("=" * 60)
        print("🔐 ENCRYPTED LLM CHAT SESSION")
        print("=" * 60)
        print(f"Model: {self.model_name}")
        print(f"Encryption: {self.key_type.upper()}")
        print("Type 'quit' to exit, 'info' for model info")
        print("-" * 60)
        
        # Initialize model
        if not self.initialize_model():
            print("❌ Failed to initialize model. Exiting.")
            return
        
        conversation_count = 0
        
        while True:
            try:
                # Get user input
                user_input = input(f"\n💬 Your message: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Ending encrypted chat session. Goodbye!")
                    break
                
                if user_input.lower() == 'info':
                    self._show_model_info()
                    continue
                
                if not user_input:
                    continue
                
                conversation_count += 1
                print(f"\n🔄 Processing message {conversation_count}...")
                
                # Simulate user encrypting prompt (user perspective)
                print("👤 User: Encrypting prompt...")
                user_metadata = {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "user_id": "interactive_user",
                    "conversation_id": f"session_{int(time.time())}",
                    "message_number": conversation_count
                }
                
                encrypted_prompt = self.crypto.encrypt_message(
                    user_input,
                    self.model_public_key,
                    user_metadata
                )
                
                # Process with encrypted LLM
                encrypted_response = self.process_encrypted_prompt(encrypted_prompt)
                
                # Simulate user decrypting response (user perspective)
                print("👤 User: Decrypting response...")
                decrypted_response, response_metadata = self.crypto.decrypt_message(
                    encrypted_response,
                    self.user_private_key
                )
                
                print("\n" + "=" * 50)
                print(f"✨ ENCRYPTED LLM RESPONSE:")
                print(f"{decrypted_response}")
                print("=" * 50)
                
                # Show some metadata
                if response_metadata.get("generation_time_seconds"):
                    print(f"⏱️  Generation time: {response_metadata['generation_time_seconds']}s")
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error in chat session: {e}")
    
    def _show_model_info(self):
        """Show model information."""
        info = self.model_manager.get_model_info()
        print("\n" + "=" * 40)
        print("🔧 MODEL INFORMATION")
        print("=" * 40)
        for key, value in info.items():
            print(f"{key}: {value}")
        print("=" * 40)
    
    def cleanup(self):
        """Clean up resources."""
        if self.model_manager:
            self.model_manager.unload_model()
        print("🗑️  Cleaned up encrypted LLM resources")


def main():
    """Demo the encrypted LLM."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Encrypted LLM Demo")
    parser.add_argument("--model", default="tinyllama", choices=ModelManager.SUPPORTED_MODELS.keys(),
                       help="LLM model to use")
    parser.add_argument("--ecc", action="store_true", help="Use ECC instead of RSA")
    parser.add_argument("--batch", action="store_true", help="Run batch test instead of interactive")
    
    args = parser.parse_args()
    
    key_type = "ecc" if args.ecc else "rsa"
    
    try:
        # Initialize encrypted LLM
        encrypted_llm = EncryptedLLM(
            model_name=args.model,
            key_type=key_type
        )
        
        if args.batch:
            # Run batch test
            test_prompts = [
                "Hello, how are you?",
                "What is encryption?", 
                "Explain AI in simple terms.",
                "Tell me a short joke.",
                "What are the benefits of secure communication?"
            ]
            
            print("🧪 Running batch test of encrypted LLM...")
            
            for i, prompt in enumerate(test_prompts, 1):
                print(f"\n📋 Test {i}/{len(test_prompts)}")
                print("=" * 40)
                
                # Encrypt prompt
                encrypted_prompt = encrypted_llm.crypto.encrypt_message(
                    prompt,
                    encrypted_llm.model_public_key,
                    {"test_id": i, "batch": True}
                )
                
                # Process
                encrypted_response = encrypted_llm.process_encrypted_prompt(encrypted_prompt)
                
                # Decrypt response
                response, metadata = encrypted_llm.crypto.decrypt_message(
                    encrypted_response,
                    encrypted_llm.user_private_key
                )
                
                print(f"✨ Result: {response}")
                time.sleep(1)  # Brief pause between tests
        else:
            # Run interactive session
            encrypted_llm.chat_session()
        
        # Cleanup
        encrypted_llm.cleanup()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\nMake sure you have:")
        print("1. Generated certificates: python crypto/generate_certs.py")
        print("2. Installed requirements: pip install -r requirements.txt")


if __name__ == "__main__":
    main()
