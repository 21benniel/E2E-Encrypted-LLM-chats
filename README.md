# 🔐 Encrypted LLM Chat

A complete end-to-end encrypted chat application that enables secure conversations with local Large Language Models. Your prompts are encrypted before being sent to the AI, and responses are encrypted before being returned to you.

![Project Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 🌟 Features

- **🔐 End-to-End Encryption**: RSA-2048 or ECC-P256 encryption with AES-256-GCM
- **🤖 Local AI Models**: Phi-3, Mistral, TinyLlama - no cloud dependencies
- **🌐 Modern Web UI**: Beautiful Streamlit and Gradio interfaces
- **📜 Certificate Security**: Self-signed certificates for authentication
- **📊 Real-time Analytics**: Performance metrics and encryption status
- **💾 Chat Export**: Save encrypted conversations as JSON
- **🔧 Easy Setup**: One-command installation and deployment

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate certificates
python crypto/generate_certs.py

# 3. Launch web interface
python launch_streamlit.py  # or python launch_gradio.py
```

### Option 2: CLI Demo
```bash
python demo/week2_encrypted_llm_demo.py --model tinyllama
```

### Option 3: Docker
```bash
docker-compose up --build
```

**Access at**: http://localhost:8501 (Streamlit) or http://localhost:7860 (Gradio)

## 🛡️ How It Works

```
👤 User Message → 🔐 Encrypt → 🤖 AI Model → 🔓 Decrypt → 🧠 Process → 🔐 Encrypt → 👤 User
```

1. **User encrypts** message with AI model's public key
2. **AI model decrypts** message with its private key
3. **AI processes** message with local LLM (Phi-3, Mistral, etc.)
4. **AI encrypts** response with user's public key  
5. **User decrypts** response with their private key

**Result**: End-to-end encrypted AI conversations with zero plaintext exposure!

## 🎯 Supported Models

| Model | Size | Description | RAM Req. |
|-------|------|-------------|----------|
| **TinyLlama** | 1.1B | Ultra lightweight, perfect for testing | 4GB |
| **Phi-3 Mini** | 3.8B | Microsoft's efficient model, great balance | 8GB |
| **Mistral 7B** | 7B | High-quality responses, production-ready | 16GB |

*All models run locally - no data sent to external servers!*

## 📁 Project Structure

```
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
│   ├── encrypted_chat_demo.py      # Week 1 crypto demo
│   └── week2_encrypted_llm_demo.py # Week 2 LLM demo
├── 📁 certs/               # Generated certificates (git-ignored)
├── 🐳 Dockerfile           # Container deployment
└── 📚 docs/                # Comprehensive documentation
```

## 🔧 Installation & Setup

### System Requirements
- **Python**: 3.10 or higher
- **RAM**: 8GB+ (16GB recommended)
- **Storage**: 10GB+ for models
- **GPU**: Optional (NVIDIA with 8GB+ VRAM for faster inference)

### Detailed Setup
See our comprehensive [SETUP_GUIDE.md](SETUP_GUIDE.md) for step-by-step instructions.

### Quick Install
```bash
# Clone repository
git clone <your-repo-url>
cd encrypted-llm-chat

# Install in virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate encryption certificates
python crypto/generate_certs.py

# Test installation
python demo/week2_encrypted_llm_demo.py --model tinyllama --batch

# Launch web interface
python launch_streamlit.py
```

## 🌐 Web Interfaces

### Streamlit Interface
- **Modern design** with gradient themes
- **Real-time chat** with message history
- **Encryption visualization** and metrics
- **Model configuration** and performance analytics
- **Chat export** functionality

### Gradio Interface  
- **Clean, intuitive** chat interface
- **Live encryption status** updates
- **Advanced settings** panel
- **Security information** display
- **Export capabilities**

Both interfaces provide the same core functionality with different UX approaches.

## 🔐 Security Features

- **End-to-End Encryption**: Messages never exist in plaintext during transmission
- **Certificate-Based Auth**: Self-signed X.509 certificates for identity verification
- **Multiple Algorithms**: RSA-2048 and ECC-P256 support
- **Perfect Forward Secrecy**: ECC mode provides ephemeral key exchange
- **Local Processing**: All AI inference happens locally, no cloud dependencies
- **No Data Leakage**: Conversation history encrypted and stored locally

## 📊 Development Timeline

### ✅ Week 1: Crypto Foundations
- RSA/ECC key pair generation
- Self-signed certificate creation  
- Hybrid encryption (RSA/ECC + AES-256-GCM)
- Secure message exchange demo

### ✅ Week 2: LLM Integration
- Local model support (Phi-3, Mistral, TinyLlama)
- Encrypted inference pipeline
- Memory optimization with quantization
- CLI chat application

### ✅ Week 3: Web Chat UI
- Streamlit interface with modern design
- Gradio alternative interface
- Real-time chat with encryption status
- Performance analytics and metrics

### ✅ Week 4: Packaging & Deployment
- Docker containerization
- Comprehensive documentation
- Cloud deployment guides
- Production-ready setup

## 🚀 Deployment Options

### Local Development
```bash
python launch_streamlit.py
```

### Docker
```bash
docker-compose up --build
```

### Cloud Deployment
- **Hugging Face Spaces**: Direct upload support
- **Google Cloud Run**: Containerized deployment
- **AWS ECS/Fargate**: Scalable cloud hosting
- **Self-hosted**: VPS or dedicated server

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🎯 Use Cases

- **🏥 Healthcare**: Secure medical AI consultations
- **💼 Enterprise**: Confidential business AI assistance  
- **🔬 Research**: Privacy-preserving AI experiments
- **📚 Education**: Cryptography and AI security demos
- **🏠 Personal**: Private AI conversations at home
- **🛡️ Security**: Sensitive data processing with AI

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **🐛 Bug Reports**: Found an issue? Open a GitHub issue
2. **💡 Feature Requests**: Have an idea? Let's discuss it
3. **🔧 Code Contributions**: Submit pull requests
4. **📚 Documentation**: Help improve our guides
5. **🧪 Testing**: Test on different systems and models

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Microsoft**: Phi-3 models
- **Mistral AI**: Mistral models  
- **TinyLlama Team**: Ultra-efficient models
- **Hugging Face**: Transformers library
- **Python Cryptography**: Secure encryption primitives
- **Streamlit & Gradio**: Amazing web frameworks

## 📞 Support

- **📖 Documentation**: Start with [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **🐛 Issues**: GitHub Issues for bug reports
- **💬 Discussions**: GitHub Discussions for questions
- **📧 Contact**: [Your contact information]

## 🌟 Star History

If you find this project useful, please give it a ⭐ on GitHub!

---

**🔐 Built for privacy. Designed for security. Made for everyone.** 

*Experience the future of encrypted AI conversations today!*
