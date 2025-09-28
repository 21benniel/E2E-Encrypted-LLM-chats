#!/usr/bin/env python3
"""
Week 2 Demo: Encrypted LLM Chat with Real AI

This demonstrates the complete Week 2 deliverable:
- User encrypts prompt with Model's public key
- Model decrypts prompt with its private key  
- Model runs actual LLM inference
- Model encrypts response with User's public key
- User decrypts final response with their private key

Complete end-to-end encrypted AI chat!
"""

import time
import argparse
from typing import List, Dict, Any

from llm.encrypted_llm import EncryptedLLM
from llm.model_manager import ModelManager


def run_comprehensive_demo(model_name: str = "tinyllama", key_type: str = "rsa"):
    """Run a comprehensive demo showing all Week 2 features."""
    
    print("=" * 70)
    print("🚀 WEEK 2 DEMO: ENCRYPTED LLM CHAT")
    print("=" * 70)
    print(f"📦 Model: {model_name}")
    print(f"🔐 Encryption: {key_type.upper()}")
    print(f"🎯 Goal: Real AI responses with end-to-end encryption")
    print("-" * 70)
    
    try:
        # Initialize encrypted LLM
        print("🔧 Initializing Encrypted LLM...")
        encrypted_llm = EncryptedLLM(model_name=model_name, key_type=key_type)
        
        # Show model info
        model_info = encrypted_llm.model_manager.get_model_info()
        print(f"\n📊 Model Information:")
        print(f"   • Description: {model_info['description']}")
        print(f"   • Max Memory: {model_info['max_memory_gb']}GB")
        print(f"   • Quantized: {model_info['quantize']}")
        print(f"   • GPU Available: {model_info['gpu_available']}")
        if model_info['gpu_available']:
            print(f"   • GPU Memory: {model_info['gpu_memory_gb']:.1f}GB")
        
        # Test prompts showcasing different capabilities
        test_scenarios = [
            {
                "category": "🤝 Basic Interaction",
                "prompts": [
                    "Hello! Can you introduce yourself?",
                    "How are you doing today?"
                ]
            },
            {
                "category": "🔐 Security & Encryption",  
                "prompts": [
                    "What is end-to-end encryption and why is it important?",
                    "Explain how public key cryptography works in simple terms."
                ]
            },
            {
                "category": "🤖 AI & Technology",
                "prompts": [
                    "What are the benefits of running AI models locally vs in the cloud?",
                    "How do large language models work?"
                ]
            },
            {
                "category": "🧠 Reasoning & Problem Solving",
                "prompts": [
                    "If I have 3 apples and buy 2 more, then give away 1, how many do I have?",
                    "What are some creative uses for encrypted AI assistants?"
                ]
            }
        ]
        
        total_tests = sum(len(scenario["prompts"]) for scenario in test_scenarios)
        test_count = 0
        
        print(f"\n🧪 Running {total_tests} encrypted AI tests...")
        
        # Process each test scenario
        for scenario in test_scenarios:
            print(f"\n{scenario['category']}")
            print("=" * 50)
            
            for prompt in scenario["prompts"]:
                test_count += 1
                print(f"\n📝 Test {test_count}/{total_tests}: {prompt}")
                print("-" * 40)
                
                # Step 1: User encrypts prompt
                print("👤 USER: Encrypting prompt...")
                start_time = time.time()
                
                user_metadata = {
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "test_scenario": scenario["category"],
                    "test_number": test_count,
                    "user_id": "demo_user"
                }
                
                encrypted_prompt = encrypted_llm.crypto.encrypt_message(
                    prompt,
                    encrypted_llm.model_public_key,
                    user_metadata
                )
                
                print(f"   🔐 Encrypted prompt size: {len(encrypted_prompt)} chars")
                
                # Step 2: Model processes encrypted prompt (full LLM pipeline)
                print("🤖 MODEL: Processing encrypted prompt...")
                encrypted_response = encrypted_llm.process_encrypted_prompt(
                    encrypted_prompt,
                    generation_params={
                        "max_length": 200,  # Shorter responses for demo
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                )
                
                # Step 3: User decrypts response
                print("👤 USER: Decrypting response...")
                decrypted_response, response_metadata = encrypted_llm.crypto.decrypt_message(
                    encrypted_response,
                    encrypted_llm.user_private_key
                )
                
                total_time = time.time() - start_time
                
                # Display results
                print(f"\n✨ ENCRYPTED AI RESPONSE:")
                print(f"📄 {decrypted_response}")
                
                print(f"\n📊 Performance:")
                print(f"   • Total time: {total_time:.2f}s")
                print(f"   • Generation time: {response_metadata.get('generation_time_seconds', 'N/A')}s")
                print(f"   • Response length: {len(decrypted_response)} chars")
                
                # Brief pause between tests
                time.sleep(1)
        
        print("\n" + "=" * 70)
        print("🎉 WEEK 2 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("✅ Achievements:")
        print("   • End-to-end encrypted AI chat working")
        print("   • Real LLM responses (not simulated)")
        print("   • Certificate-based security")
        print("   • Local AI inference (privacy-first)")
        print("   • Multiple test scenarios passed")
        
        print(f"\n🔐 Security Summary:")
        print("   • All prompts encrypted before transmission")
        print("   • Model never sees plaintext during 'transmission'")
        print("   • All responses encrypted before return")
        print("   • Only endpoints can decrypt content")
        
        # Cleanup
        encrypted_llm.cleanup()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return False


def run_interactive_session(model_name: str = "tinyllama", key_type: str = "rsa"):
    """Run an interactive encrypted LLM chat session."""
    
    print("=" * 60)
    print("💬 INTERACTIVE ENCRYPTED LLM CHAT")
    print("=" * 60)
    
    try:
        encrypted_llm = EncryptedLLM(model_name=model_name, key_type=key_type)
        encrypted_llm.chat_session()
        
    except Exception as e:
        print(f"❌ Interactive session failed: {e}")


def main():
    """Main demo function with options."""
    parser = argparse.ArgumentParser(description="Week 2 Encrypted LLM Demo")
    parser.add_argument("--model", default="tinyllama", 
                       choices=list(ModelManager.SUPPORTED_MODELS.keys()),
                       help="LLM model to use")
    parser.add_argument("--ecc", action="store_true", help="Use ECC instead of RSA")
    parser.add_argument("--interactive", action="store_true", 
                       help="Run interactive session instead of demo")
    parser.add_argument("--list-models", action="store_true",
                       help="List available models and exit")
    
    args = parser.parse_args()
    
    if args.list_models:
        print("📋 Available Models:")
        for name, desc in ModelManager.list_supported_models().items():
            print(f"   • {name}: {desc}")
        return
    
    key_type = "ecc" if args.ecc else "rsa"
    
    print("🔐 ENCRYPTED LLM CHAT - WEEK 2")
    print(f"Selected: {args.model} with {key_type.upper()} encryption")
    print()
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    try:
        from crypto.key_manager import KeyManager
        key_manager = KeyManager()
        
        # Check if certificates exist
        required_files = [
            f"user_{key_type}_private_key.pem",
            f"model_{key_type}_private_key.pem"
        ]
        
        missing_files = []
        for file in required_files:
            try:
                key_manager.load_private_key(file)
            except FileNotFoundError:
                missing_files.append(file)
        
        if missing_files:
            print("❌ Missing certificate files:")
            for file in missing_files:
                print(f"   • {file}")
            print(f"\nRun: python crypto/generate_certs.py {'--ecc' if key_type == 'ecc' else ''}")
            return
        
        print("✅ Certificates found")
        
    except Exception as e:
        print(f"❌ Prerequisite check failed: {e}")
        return
    
    # Run selected mode
    if args.interactive:
        run_interactive_session(args.model, key_type)
    else:
        success = run_comprehensive_demo(args.model, key_type)
        if success:
            print("\n🚀 Ready for Week 3: Building the Web UI!")
        else:
            print("\n❌ Demo failed. Check error messages above.")


if __name__ == "__main__":
    main()
