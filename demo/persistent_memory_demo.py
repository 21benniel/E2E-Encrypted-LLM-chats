#!/usr/bin/env python3
"""
Encrypted LLM with Persistent Memory Demo

Demonstrates the new conversation memory system with E2E encryption.
Shows how conversations are saved, loaded, and used for context.
"""

import time
import json
from pathlib import Path

try:
    from llm.encrypted_llm import EncryptedLLM
    from crypto.key_manager import KeyManager
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    print(f"Components not available: {e}")


def ensure_keys_exist():
    """Ensure RSA keys exist for the demo."""
    key_manager = KeyManager()
    
    # Check if keys exist
    certs_dir = Path("certs")
    user_private = certs_dir / "user_rsa_private_key.pem"
    model_private = certs_dir / "model_rsa_private_key.pem"
    
    if not (user_private.exists() and model_private.exists()):
        print("🔑 Generating RSA keys for memory demo...")
        key_manager.setup_user_keys(use_ecc=False)
        key_manager.setup_model_keys(use_ecc=False)
        print("✅ Keys generated successfully")
    else:
        print("✅ Keys already exist")


def demo_conversation_memory():
    """Demonstrate persistent conversation memory."""
    print("🔐 ENCRYPTED LLM WITH PERSISTENT MEMORY DEMO")
    print("=" * 60)
    
    # Ensure keys exist
    ensure_keys_exist()
    
    # Initialize encrypted LLM with memory enabled
    print("\n🚀 Initializing Encrypted LLM with Memory...")
    encrypted_llm = EncryptedLLM(
        model_name="tinyllama",
        key_type="rsa",
        enable_memory=True,
        memory_storage_dir="demo_conversations"
    )
    
    if not encrypted_llm.initialize_model():
        print("❌ Failed to initialize model. Exiting.")
        return
    
    # Create a new conversation
    print("\n📝 Creating new conversation...")
    conversation_id = encrypted_llm.create_conversation(
        title="AI Learning Session",
        tags=["demo", "learning", "ai"]
    )
    
    if not conversation_id:
        print("❌ Failed to create conversation")
        return
    
    print(f"✅ Created conversation: {conversation_id}")
    
    # Demo conversation with memory
    demo_messages = [
        "Hello! I'm learning about AI. Can you explain what machine learning is?",
        "That's helpful! Can you give me an example of supervised learning?",
        "What about unsupervised learning? How is it different?",
        "Can you remind me what we discussed about supervised learning earlier?"
    ]
    
    print(f"\n💬 Starting conversation with {len(demo_messages)} messages...")
    
    for i, user_message in enumerate(demo_messages, 1):
        print(f"\n--- Message {i}/{len(demo_messages)} ---")
        print(f"👤 User: {user_message}")
        
        # Encrypt user message
        encrypted_prompt = encrypted_llm.crypto.encrypt_message(
            user_message,
            encrypted_llm.model_public_key,
            {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "message_number": i,
                "demo": True
            }
        )
        
        # Process with memory context
        encrypted_response = encrypted_llm.process_encrypted_prompt(
            encrypted_prompt,
            conversation_id=conversation_id,
            use_context=True,
            generation_params={
                "max_length": 200,
                "temperature": 0.7
            }
        )
        
        # Decrypt response
        decrypted_response, response_metadata = encrypted_llm.crypto.decrypt_message(
            encrypted_response,
            encrypted_llm.user_private_key
        )
        
        print(f"🤖 Assistant: {decrypted_response}")
        
        # Show if context was used
        if response_metadata.get("context_used"):
            print("   🧠 (Used conversation context)")
        
        print(f"   ⏱️  Generation time: {response_metadata.get('generation_time_seconds', 0):.2f}s")
        
        # Small delay between messages
        time.sleep(1)
    
    # Show conversation history
    print(f"\n📖 Complete Conversation History:")
    print("=" * 50)
    
    history = encrypted_llm.get_conversation_history(conversation_id)
    for msg in history:
        role_icon = "👤" if msg["role"] == "user" else "🤖"
        print(f"{role_icon} {msg['role'].title()}: {msg['content']}")
        print(f"   Time: {msg['timestamp']}")
        print()
    
    # Show memory statistics
    print("📊 Memory System Statistics:")
    print("=" * 30)
    stats = encrypted_llm.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # List all conversations
    print(f"\n📋 All Conversations:")
    conversations = encrypted_llm.list_conversations()
    for conv in conversations:
        print(f"  📝 {conv['title']} ({conv['message_count']} messages)")
        print(f"     ID: {conv['id']}")
        print(f"     Updated: {conv['last_updated']}")
        print(f"     Tags: {conv['tags']}")
        print()
    
    # Export conversation
    print("📤 Exporting conversation...")
    export_data = encrypted_llm.export_conversation(conversation_id)
    if export_data:
        export_file = f"conversation_export_{int(time.time())}.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"✅ Conversation exported to: {export_file}")
    
    print("\n🎉 Memory demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("✅ Persistent encrypted conversation storage")
    print("✅ Context-aware AI responses using conversation history")
    print("✅ Conversation management (create, list, export)")
    print("✅ End-to-end encryption maintained throughout")
    print("✅ Metadata tracking and statistics")


def demo_memory_persistence():
    """Demonstrate that conversations persist across sessions."""
    print("\n🔄 PERSISTENCE DEMO")
    print("=" * 30)
    
    # Initialize a new instance (simulating app restart)
    encrypted_llm = EncryptedLLM(
        model_name="tinyllama",
        key_type="rsa",
        enable_memory=True,
        memory_storage_dir="demo_conversations"
    )
    
    # List existing conversations
    conversations = encrypted_llm.list_conversations()
    
    if conversations:
        print(f"✅ Found {len(conversations)} existing conversations:")
        for conv in conversations:
            print(f"  📝 {conv['title']} ({conv['message_count']} messages)")
        
        # Load the most recent conversation
        latest_conv = conversations[0]
        conv_id = latest_conv['id']
        
        print(f"\n🔍 Loading conversation: {latest_conv['title']}")
        history = encrypted_llm.get_conversation_history(conv_id)
        
        print("📖 Previous conversation context:")
        for msg in history[-4:]:  # Show last 4 messages
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            print(f"  {role_icon} {msg['content'][:100]}...")
        
        print("\n✅ Conversation persistence verified!")
    else:
        print("ℹ️  No existing conversations found. Run the main demo first.")


def interactive_memory_demo():
    """Interactive demo where user can chat with memory."""
    print("\n💬 INTERACTIVE MEMORY DEMO")
    print("=" * 30)
    print("Type 'quit' to exit, 'new' for new conversation, 'list' to see conversations")
    
    encrypted_llm = EncryptedLLM(
        model_name="tinyllama",
        key_type="rsa",
        enable_memory=True,
        memory_storage_dir="demo_conversations"
    )
    
    if not encrypted_llm.initialize_model():
        print("❌ Failed to initialize model")
        return
    
    current_conversation_id = None
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if user_input.lower() == 'new':
                title = input("📝 Conversation title (or press Enter): ").strip()
                if not title:
                    title = f"Chat {time.strftime('%H:%M')}"
                
                current_conversation_id = encrypted_llm.create_conversation(title=title)
                print(f"✅ Created new conversation: {current_conversation_id}")
                continue
            
            if user_input.lower() == 'list':
                conversations = encrypted_llm.list_conversations(10)
                print("\n📋 Recent Conversations:")
                for i, conv in enumerate(conversations, 1):
                    print(f"  {i}. {conv['title']} ({conv['message_count']} messages)")
                continue
            
            if not user_input:
                continue
            
            # Create conversation if none exists
            if not current_conversation_id:
                current_conversation_id = encrypted_llm.create_conversation(
                    title=f"Interactive Chat {time.strftime('%H:%M')}"
                )
                print(f"✅ Created conversation: {current_conversation_id}")
            
            # Encrypt and process message
            encrypted_prompt = encrypted_llm.crypto.encrypt_message(
                user_input,
                encrypted_llm.model_public_key,
                {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
            )
            
            encrypted_response = encrypted_llm.process_encrypted_prompt(
                encrypted_prompt,
                conversation_id=current_conversation_id,
                use_context=True
            )
            
            # Decrypt and show response
            response, metadata = encrypted_llm.crypto.decrypt_message(
                encrypted_response,
                encrypted_llm.user_private_key
            )
            
            context_indicator = " 🧠" if metadata.get("context_used") else ""
            print(f"🤖 Assistant{context_indicator}: {response}")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Interactive demo ended!")


def main():
    """Main demo function."""
    if not COMPONENTS_AVAILABLE:
        print("❌ Required components not available. Please install dependencies.")
        return
    
    print("🔐 ENCRYPTED LLM PERSISTENT MEMORY DEMO")
    print("=" * 60)
    print("This demo shows how conversation memory works with E2E encryption.")
    print()
    
    demos = {
        "1": ("Full Memory Demo", demo_conversation_memory),
        "2": ("Persistence Demo", demo_memory_persistence),
        "3": ("Interactive Demo", interactive_memory_demo),
        "4": ("All Demos", lambda: [demo_conversation_memory(), demo_memory_persistence()])
    }
    
    print("Choose a demo:")
    for key, (name, _) in demos.items():
        print(f"  {key}. {name}")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice in demos:
        name, demo_func = demos[choice]
        print(f"\n🚀 Running: {name}")
        demo_func()
    else:
        print("Invalid choice. Running full demo...")
        demo_conversation_memory()


if __name__ == "__main__":
    main()
