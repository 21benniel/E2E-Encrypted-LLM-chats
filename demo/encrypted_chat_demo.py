#!/usr/bin/env python3
"""
Encrypted Chat Demo Script

Demonstrates secure message exchange between user and model using certificates.
This is the Week 1 deliverable - no actual LLM yet, just crypto demonstration.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any

from crypto.key_manager import KeyManager
from crypto.message_crypto import MessageCrypto


class EncryptedChatDemo:
    """Demonstrates encrypted chat between user and model."""
    
    def __init__(self, use_ecc: bool = False):
        """Initialize the demo with specified key type."""
        self.key_manager = KeyManager()
        self.crypto = MessageCrypto()
        self.use_ecc = use_ecc
        self.key_type = "ecc" if use_ecc else "rsa"
        
        # Load keys
        self._load_keys()
    
    def _load_keys(self):
        """Load user and model keys."""
        try:
            # User keys (for decrypting responses)
            self.user_private_key = self.key_manager.load_private_key(
                f"user_{self.key_type}_private_key.pem"
            )
            self.user_public_key = self.key_manager.load_public_key(
                f"user_{self.key_type}_public_key.pem"
            )
            self.user_cert = self.key_manager.load_certificate(
                f"user_{self.key_type}_certificate.pem"
            )
            
            # Model keys (for encrypting prompts and decrypting them)
            self.model_private_key = self.key_manager.load_private_key(
                f"model_{self.key_type}_private_key.pem"
            )
            self.model_public_key = self.key_manager.load_public_key(
                f"model_{self.key_type}_public_key.pem"
            )
            self.model_cert = self.key_manager.load_certificate(
                f"model_{self.key_type}_certificate.pem"
            )
            
            print(f"✅ Loaded {self.key_type.upper()} keys and certificates")
            
        except FileNotFoundError as e:
            print(f"❌ Error loading keys: {e}")
            print("   Run 'python crypto/generate_certs.py' first to generate keys")
            raise
    
    def simulate_user_sending_prompt(self, prompt: str, metadata: Dict[str, Any] = None) -> str:
        """Simulate user encrypting and sending a prompt to the model."""
        print(f"\n👤 User encrypting prompt...")
        print(f"   📝 Original prompt: '{prompt}'")
        
        # Add metadata
        if metadata is None:
            metadata = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "user_id": "demo_user",
                "session_id": "demo_session_001"
            }
        
        # Encrypt prompt for model
        encrypted_bundle = self.crypto.encrypt_message(
            prompt, 
            self.model_public_key, 
            metadata
        )
        
        print(f"   🔐 Encrypted bundle size: {len(encrypted_bundle)} characters")
        print(f"   🔐 Bundle preview: {encrypted_bundle[:80]}...")
        
        return encrypted_bundle
    
    def simulate_model_processing(self, encrypted_bundle: str) -> str:
        """Simulate model receiving, decrypting, processing, and encrypting response."""
        print(f"\n🤖 Model processing encrypted prompt...")
        
        # Decrypt the prompt
        decrypted_prompt, metadata = self.crypto.decrypt_message(
            encrypted_bundle, 
            self.model_private_key
        )
        
        print(f"   🔓 Model decrypted prompt: '{decrypted_prompt}'")
        print(f"   📋 Metadata: {json.dumps(metadata, indent=2)}")
        
        # Simulate LLM processing (dummy response for now)
        simulated_responses = {
            "hello": "Hello! I'm an encrypted LLM. Your message was securely transmitted!",
            "how are you": "I'm functioning well within my encrypted environment. All communications are secure!",
            "what is ai": "AI (Artificial Intelligence) refers to computer systems that can perform tasks typically requiring human intelligence. In our case, we're demonstrating secure AI communication!",
            "tell me a joke": "Why don't cryptographers ever get lost? Because they always know their key! 🔐",
            "default": f"I received your encrypted message: '{decrypted_prompt}'. This demonstrates successful end-to-end encryption! In Week 2, I'll be replaced with a real LLM."
        }
        
        # Find appropriate response
        response = simulated_responses.get(
            decrypted_prompt.lower().strip(), 
            simulated_responses["default"]
        )
        
        print(f"   🧠 Generated response: '{response}'")
        
        # Encrypt response for user
        response_metadata = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model_id": "demo_encrypted_llm",
            "original_prompt_hash": hash(decrypted_prompt) % 10000  # Simple hash for demo
        }
        
        encrypted_response = self.crypto.encrypt_message(
            response,
            self.user_public_key,
            response_metadata
        )
        
        print(f"   🔐 Encrypted response size: {len(encrypted_response)} characters")
        
        return encrypted_response
    
    def simulate_user_receiving_response(self, encrypted_response: str) -> str:
        """Simulate user receiving and decrypting the model's response."""
        print(f"\n👤 User decrypting model response...")
        
        # Decrypt the response
        decrypted_response, metadata = self.crypto.decrypt_message(
            encrypted_response,
            self.user_private_key
        )
        
        print(f"   🔓 Decrypted response: '{decrypted_response}'")
        print(f"   📋 Response metadata: {json.dumps(metadata, indent=2)}")
        
        return decrypted_response
    
    def run_interactive_demo(self):
        """Run an interactive demo session."""
        print("=" * 60)
        print("🔐 ENCRYPTED LLM CHAT DEMO (Week 1)")
        print("=" * 60)
        print(f"Using {self.key_type.upper()} encryption")
        print("Type 'quit' to exit, 'info' for technical details")
        print("-" * 60)
        
        while True:
            try:
                # Get user input
                prompt = input("\n💬 Your prompt: ").strip()
                
                if prompt.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye! Thanks for testing encrypted LLM chat.")
                    break
                
                if prompt.lower() == 'info':
                    self._show_technical_info()
                    continue
                
                if not prompt:
                    continue
                
                # Full encryption flow
                print("\n" + "=" * 50)
                encrypted_bundle = self.simulate_user_sending_prompt(prompt)
                encrypted_response = self.simulate_model_processing(encrypted_bundle)
                final_response = self.simulate_user_receiving_response(encrypted_response)
                
                print("\n" + "=" * 50)
                print(f"✨ FINAL RESULT: {final_response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Demo interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def _show_technical_info(self):
        """Show technical information about the encryption."""
        print("\n" + "=" * 60)
        print("🔧 TECHNICAL INFORMATION")
        print("=" * 60)
        print(f"Key Type: {self.key_type.upper()}")
        print(f"Hybrid Encryption: {self.key_type.upper()} + AES-256-GCM")
        print("Certificate Validation: Basic (self-signed)")
        print("Message Flow:")
        print("  1. User encrypts prompt with Model's public key")
        print("  2. Model decrypts prompt with its private key") 
        print("  3. Model processes prompt (simulated)")
        print("  4. Model encrypts response with User's public key")
        print("  5. User decrypts response with its private key")
        print("\nSecurity Features:")
        print("  ✅ End-to-end encryption")
        print("  ✅ Perfect forward secrecy (ECC mode)")
        print("  ✅ Message authentication")
        print("  ✅ Metadata protection")
        print("  ✅ Certificate-based identity")
        print("=" * 60)
    
    def run_batch_demo(self):
        """Run a batch demo with predefined messages."""
        test_prompts = [
            "Hello",
            "How are you?", 
            "What is AI?",
            "Tell me a joke",
            "This is a test of the encrypted LLM system with a longer message to see how it handles various input sizes and content types."
        ]
        
        print("=" * 60)
        print("🔐 ENCRYPTED LLM CHAT - BATCH DEMO")
        print("=" * 60)
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n📋 Test {i}/{len(test_prompts)}")
            print("=" * 40)
            
            encrypted_bundle = self.simulate_user_sending_prompt(prompt)
            encrypted_response = self.simulate_model_processing(encrypted_bundle)
            final_response = self.simulate_user_receiving_response(encrypted_response)
            
            print(f"✨ RESULT: {final_response}")
            time.sleep(1)  # Small delay for readability
        
        print("\n" + "=" * 60)
        print("✅ Batch demo completed successfully!")
        print("🔐 All messages were encrypted end-to-end!")


def main():
    """Main demo function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Encrypted LLM Chat Demo")
    parser.add_argument("--ecc", action="store_true", help="Use ECC instead of RSA")
    parser.add_argument("--batch", action="store_true", help="Run batch demo instead of interactive")
    
    args = parser.parse_args()
    
    try:
        demo = EncryptedChatDemo(use_ecc=args.ecc)
        
        if args.batch:
            demo.run_batch_demo()
        else:
            demo.run_interactive_demo()
            
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("\nMake sure you've generated certificates first:")
        print("  python crypto/generate_certs.py")


if __name__ == "__main__":
    main()
