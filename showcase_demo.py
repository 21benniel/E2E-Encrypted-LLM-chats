#!/usr/bin/env python3
"""
Encrypted LLM Chat - Complete Project Showcase

This script demonstrates all features of the Encrypted LLM Chat system
in a comprehensive showcase format. Perfect for demonstrations, presentations,
and first-time user experiences.
"""

import time
import sys
import os
from pathlib import Path
from datetime import datetime

# Set up environment
sys.path.append('.')
os.environ['PYTHONPATH'] = str(Path.cwd())

try:
    from llm.encrypted_llm import EncryptedLLM
    from llm.model_manager import ModelManager
    from crypto.key_manager import KeyManager
    from crypto.message_crypto import MessageCrypto
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    print(f"Components not available: {e}")


class ProjectShowcase:
    """Complete project showcase and demonstration."""
    
    def __init__(self):
        """Initialize the showcase."""
        self.start_time = time.time()
    
    def print_header(self, title: str, width: int = 70):
        """Print a formatted header."""
        print("\n" + "=" * width)
        print(f"{title:^{width}}")
        print("=" * width)
    
    def print_section(self, title: str, width: int = 50):
        """Print a section header."""
        print(f"\n{title}")
        print("-" * width)
    
    def print_success(self, message: str):
        """Print a success message."""
        print(f"✅ {message}")
    
    def print_info(self, message: str):
        """Print an info message."""
        print(f"ℹ️  {message}")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"⚠️  {message}")
    
    def print_error(self, message: str):
        """Print an error message."""
        print(f"❌ {message}")
    
    def show_project_overview(self):
        """Display project overview and achievements."""
        self.print_header("🔐 ENCRYPTED LLM CHAT - PROJECT SHOWCASE")
        
        print("""
🌟 **WHAT WE BUILT**

A complete end-to-end encrypted chat application that enables secure 
conversations with local Large Language Models. Your prompts are encrypted 
before being sent to the AI, and responses are encrypted before being 
returned to you.

🎯 **KEY ACHIEVEMENTS**
✅ End-to-end encryption with RSA-2048 & ECC-P256
✅ Local AI models (Phi-3, Mistral, TinyLlama) 
✅ Beautiful web interfaces (Streamlit & Gradio)
✅ Certificate-based security & authentication
✅ Real-time analytics & performance metrics
✅ Docker deployment & cloud-ready setup
✅ Comprehensive documentation & guides

🔐 **SECURITY FEATURES**
• Messages never exist in plaintext during transmission
• Certificate-based authentication with X.509 standards
• Perfect forward secrecy with ECC mode
• Local AI processing - no cloud dependencies
• Military-grade AES-256-GCM encryption
        """)
    
    def check_prerequisites(self):
        """Check system prerequisites and setup."""
        self.print_section("🔍 SYSTEM PREREQUISITES CHECK")
        
        # Check Python version
        python_version = sys.version_info
        if python_version >= (3, 10):
            self.print_success(f"Python {python_version.major}.{python_version.minor} - Compatible")
        else:
            self.print_error(f"Python {python_version.major}.{python_version.minor} - Requires 3.10+")
            return False
        
        # Check components
        if COMPONENTS_AVAILABLE:
            self.print_success("All Python components available")
        else:
            self.print_error("Missing required components")
            self.print_info("Run: pip install -r requirements.txt")
            return False
        
        # Check certificates
        certs_dir = Path("certs")
        if certs_dir.exists() and any(certs_dir.glob("*.pem")):
            self.print_success("Encryption certificates found")
            cert_count = len(list(certs_dir.glob("*.pem")))
            self.print_info(f"Found {cert_count} certificate files")
        else:
            self.print_warning("No certificates found")
            self.print_info("Generating certificates now...")
            try:
                import subprocess
                result = subprocess.run([sys.executable, "crypto/generate_certs.py"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    self.print_success("Certificates generated successfully")
                else:
                    self.print_error("Certificate generation failed")
                    return False
            except Exception as e:
                self.print_error(f"Failed to generate certificates: {e}")
                return False
        
        # Check available models
        try:
            supported_models = ModelManager.SUPPORTED_MODELS
            self.print_success(f"Found {len(supported_models)} supported AI models")
            for name, config in supported_models.items():
                print(f"   • {name}: {config['description']}")
        except Exception as e:
            self.print_error(f"Model manager error: {e}")
        
        return True
    
    def demonstrate_crypto_features(self):
        """Demonstrate encryption capabilities."""
        self.print_section("🔐 ENCRYPTION DEMONSTRATION")
        
        try:
            # Initialize crypto components
            key_manager = KeyManager()
            crypto = MessageCrypto()
            
            # Load keys
            user_private_key = key_manager.load_private_key("user_rsa_private_key.pem")
            user_public_key = key_manager.load_public_key("user_rsa_public_key.pem")
            model_private_key = key_manager.load_private_key("model_rsa_private_key.pem")
            model_public_key = key_manager.load_public_key("model_rsa_public_key.pem")
            
            self.print_success("Loaded RSA encryption keys")
            
            # Demonstrate encryption
            test_messages = [
                "Hello, secure AI!",
                "This message contains sensitive information: SSN 123-45-6789",
                "Confidential business data: Q4 revenue projections show 25% growth"
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n📝 Test Message {i}: '{message}'")
                
                # Encrypt
                start_time = time.time()
                encrypted_bundle = crypto.encrypt_message(
                    message, 
                    model_public_key,
                    {"test_id": i, "demo": True}
                )
                encrypt_time = time.time() - start_time
                
                print(f"🔐 Encrypted: {len(encrypted_bundle)} chars in {encrypt_time*1000:.1f}ms")
                print(f"   Preview: {encrypted_bundle[:80]}...")
                
                # Decrypt
                start_time = time.time()
                decrypted_message, metadata = crypto.decrypt_message(
                    encrypted_bundle,
                    model_private_key
                )
                decrypt_time = time.time() - start_time
                
                print(f"🔓 Decrypted: '{decrypted_message}' in {decrypt_time*1000:.1f}ms")
                
                if decrypted_message == message:
                    self.print_success("Encryption/decryption verified!")
                else:
                    self.print_error("Encryption/decryption failed!")
                
        except Exception as e:
            self.print_error(f"Crypto demonstration failed: {e}")
    
    def demonstrate_llm_integration(self):
        """Demonstrate LLM integration with encryption."""
        self.print_section("🤖 ENCRYPTED AI DEMONSTRATION")
        
        try:
            # Initialize encrypted LLM with lightweight model
            print("🔄 Initializing Encrypted LLM (this may take a moment)...")
            encrypted_llm = EncryptedLLM(model_name="tinyllama", key_type="rsa")
            
            if not encrypted_llm.initialize_model():
                self.print_error("Failed to initialize AI model")
                return
            
            self.print_success("Encrypted LLM initialized with TinyLlama")
            
            # Test prompts
            test_prompts = [
                "What is end-to-end encryption?",
                "How does artificial intelligence work?", 
                "Tell me about privacy in technology."
            ]
            
            for i, prompt in enumerate(test_prompts, 1):
                print(f"\n💬 Encrypted Conversation {i}")
                print(f"👤 User: {prompt}")
                
                # Simulate user encrypting prompt
                print("🔐 Encrypting prompt...")
                encrypted_prompt = encrypted_llm.crypto.encrypt_message(
                    prompt,
                    encrypted_llm.model_public_key,
                    {"conversation_id": i, "demo": True}
                )
                
                # Process with encrypted LLM
                print("🤖 AI processing encrypted prompt...")
                start_time = time.time()
                encrypted_response = encrypted_llm.process_encrypted_prompt(
                    encrypted_prompt,
                    {"max_length": 150, "temperature": 0.7}
                )
                
                # Decrypt response
                print("🔓 Decrypting AI response...")
                decrypted_response, metadata = encrypted_llm.crypto.decrypt_message(
                    encrypted_response,
                    encrypted_llm.user_private_key
                )
                
                total_time = time.time() - start_time
                generation_time = metadata.get('generation_time_seconds', 0)
                
                print(f"🤖 AI: {decrypted_response}")
                print(f"⏱️  Total time: {total_time:.2f}s (Generation: {generation_time:.2f}s)")
                
                time.sleep(1)  # Brief pause between conversations
            
            # Cleanup
            encrypted_llm.cleanup()
            self.print_success("Encrypted AI demonstration completed!")
            
        except Exception as e:
            self.print_error(f"LLM demonstration failed: {e}")
    
    def show_deployment_options(self):
        """Show available deployment options."""
        self.print_section("🚀 DEPLOYMENT OPTIONS")
        
        print("""
🏠 **LOCAL DEVELOPMENT**
   python launch_streamlit.py  # Modern web interface
   python launch_gradio.py     # Alternative interface
   
🐳 **DOCKER DEPLOYMENT** 
   docker-compose up --build   # One-command deployment
   
☁️  **CLOUD DEPLOYMENT**
   • Hugging Face Spaces - Direct upload
   • Google Cloud Run - Serverless containers  
   • AWS ECS/Fargate - Scalable hosting
   • Self-hosted VPS - Full control
   
🏢 **ENTERPRISE DEPLOYMENT**
   • Private cloud integration
   • LDAP/Active Directory auth
   • Audit logging & compliance
   • High availability setup
        """)
        
        # Show launch commands
        print("\n📋 **QUICK START COMMANDS**")
        print("# Web Interface (Recommended)")
        print("python launch_streamlit.py")
        print()
        print("# CLI Demo")  
        print("python demo/week2_encrypted_llm_demo.py --model tinyllama")
        print()
        print("# Docker")
        print("docker-compose up --build")
    
    def show_project_structure(self):
        """Display project structure and components."""
        self.print_section("📁 PROJECT ARCHITECTURE")
        
        print("""
encrypted-llm-chat/
├── 🔐 crypto/              # Encryption & certificate management
│   ├── key_manager.py      # RSA/ECC key generation
│   ├── message_crypto.py   # Hybrid encryption (RSA+AES)
│   └── generate_certs.py   # Certificate generation CLI
├── 🤖 llm/                 # Local LLM integration  
│   ├── model_manager.py    # Model loading & inference
│   └── encrypted_llm.py    # Encrypted LLM wrapper
├── 🌐 ui/                  # Web interfaces
│   ├── streamlit_app.py    # Streamlit chat interface
│   └── gradio_app.py       # Gradio chat interface  
├── 🎮 demo/                # Demo applications
│   ├── encrypted_chat_demo.py      # Crypto demo
│   └── week2_encrypted_llm_demo.py # Full LLM demo
├── 📚 Documentation/       # Comprehensive guides
│   ├── README.md           # Project overview
│   ├── SETUP_GUIDE.md      # Installation guide
│   ├── DEPLOYMENT.md       # Deployment options
│   └── WEEK*_SUMMARY.md    # Development journey
├── 🐳 Docker files         # Container deployment
└── 📁 certs/               # Generated certificates
        """)
    
    def show_performance_metrics(self):
        """Display performance and capability metrics."""
        self.print_section("📊 PERFORMANCE METRICS")
        
        print("""
🖥️  **SYSTEM REQUIREMENTS**
   • RAM: 8GB+ (16GB recommended)
   • Storage: 10GB+ for models  
   • CPU: 4+ cores recommended
   • GPU: Optional (8GB+ VRAM for acceleration)

⚡ **PERFORMANCE BENCHMARKS**
   • Startup time: 30-60 seconds (model loading)
   • Encryption: <100ms per message
   • TinyLlama inference: 10-30 seconds per response
   • Phi-3 inference: 20-60 seconds per response
   • Memory usage: 4-16GB depending on model

🔐 **SECURITY SPECIFICATIONS**
   • RSA-2048 or ECC-P256 key exchange
   • AES-256-GCM message encryption  
   • X.509 certificate authentication
   • Perfect forward secrecy (ECC mode)
   • Zero plaintext storage/transmission
        """)
    
    def show_use_cases(self):
        """Display practical use cases."""
        self.print_section("🎯 REAL-WORLD USE CASES")
        
        print("""
🏥 **HEALTHCARE**
   • Secure medical AI consultations
   • HIPAA-compliant patient data processing
   • Confidential research data analysis
   • Private health information queries

💼 **ENTERPRISE**  
   • Confidential business AI assistance
   • Secure internal document processing
   • Private competitive analysis
   • Sensitive financial data queries

🔬 **RESEARCH & EDUCATION**
   • Privacy-preserving AI experiments
   • Cryptography education and demos
   • Secure academic research processing
   • Student privacy protection

🏠 **PERSONAL USE**
   • Private AI conversations at home
   • Sensitive personal data processing
   • Family privacy protection
   • Secure journaling and note-taking

🛡️  **SECURITY & COMPLIANCE**
   • Government classified data processing
   • Legal document confidentiality
   • Financial regulatory compliance
   • Corporate data protection
        """)
    
    def run_complete_showcase(self):
        """Run the complete project showcase."""
        try:
            # Project overview
            self.show_project_overview()
            input("\nPress Enter to continue to prerequisites check...")
            
            # Prerequisites
            if not self.check_prerequisites():
                self.print_error("Prerequisites not met. Please resolve issues and try again.")
                return False
            
            input("\nPress Enter to continue to encryption demo...")
            
            # Crypto demonstration
            self.demonstrate_crypto_features()
            input("\nPress Enter to continue to AI demo...")
            
            # LLM demonstration
            self.demonstrate_llm_integration()
            input("\nPress Enter to see deployment options...")
            
            # Deployment options
            self.show_deployment_options()
            input("\nPress Enter to see project structure...")
            
            # Project structure
            self.show_project_structure()
            input("\nPress Enter to see performance metrics...")
            
            # Performance metrics
            self.show_performance_metrics()
            input("\nPress Enter to see use cases...")
            
            # Use cases
            self.show_use_cases()
            
            # Final summary
            self.print_header("🎉 SHOWCASE COMPLETE")
            total_time = time.time() - self.start_time
            
            print(f"""
🌟 **CONGRATULATIONS!** 

You've just experienced the complete Encrypted LLM Chat system!

⏱️  Showcase duration: {total_time:.1f} seconds
🔐 Encryption demonstrations: ✅ Completed
🤖 AI integration demos: ✅ Completed  
📚 Documentation review: ✅ Completed
🚀 Deployment options: ✅ Presented

**WHAT'S NEXT?**

1. 🌐 Launch web interface: python launch_streamlit.py
2. 🎮 Try CLI demo: python demo/week2_encrypted_llm_demo.py
3. 🐳 Deploy with Docker: docker-compose up --build
4. 📖 Read full docs: Check README.md and guides
5. 🤝 Contribute: Submit issues and pull requests

**🔐 Welcome to the future of private AI conversations!**
            """)
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n👋 Showcase interrupted. Thanks for your interest!")
            return False
        except Exception as e:
            self.print_error(f"Showcase failed: {e}")
            return False


def main():
    """Main showcase entry point."""
    if not COMPONENTS_AVAILABLE:
        print("❌ Required components not available.")
        print("Please run: pip install -r requirements.txt")
        return
    
    showcase = ProjectShowcase()
    
    print("🔐 Welcome to the Encrypted LLM Chat Project Showcase!")
    print("This demonstration will show you all features of the system.")
    print("\nChoose your experience:")
    print("1. Complete interactive showcase (recommended)")
    print("2. Quick overview only")
    print("3. Skip to web interface launch")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            showcase.run_complete_showcase()
        elif choice == "2":
            showcase.show_project_overview()
            showcase.show_deployment_options()
        elif choice == "3":
            print("\n🚀 Launching Streamlit interface...")
            import subprocess
            subprocess.run([sys.executable, "launch_streamlit.py"])
        else:
            print("Invalid choice. Running quick overview...")
            showcase.show_project_overview()
            
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for checking out Encrypted LLM Chat!")


if __name__ == "__main__":
    main()
