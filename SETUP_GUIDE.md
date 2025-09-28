# 🚀 Complete Setup Guide for Encrypted LLM Chat

This comprehensive guide will help you set up and run the Encrypted LLM Chat application from scratch.

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.10 or higher
- **RAM**: 8GB+ (16GB recommended)
- **Storage**: 10GB+ free space
- **Internet**: For initial model downloads

### Recommended Requirements
- **GPU**: NVIDIA GPU with 8GB+ VRAM (for faster inference)
- **RAM**: 16GB+ 
- **CPU**: 8+ cores
- **Storage**: 50GB+ SSD

## 🔧 Step-by-Step Installation

### Step 1: Install Python

#### Windows
1. Download Python from [python.org](https://www.python.org/downloads/)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### macOS
```bash
# Using Homebrew (recommended)
brew install python@3.10

# Or download from python.org
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.10 python3.10-pip python3.10-venv
```

### Step 2: Clone or Download the Project

#### Option A: Git Clone (if you have Git)
```bash
git clone <your-repository-url>
cd encrypted-llm-chat
```

#### Option B: Download ZIP
1. Download the project ZIP file
2. Extract to a folder (e.g., `C:\encrypted-llm-chat` or `~/encrypted-llm-chat`)
3. Open terminal/command prompt in that folder

### Step 3: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Your prompt should now show (venv)
```

### Step 4: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**Note**: This may take 5-15 minutes depending on your internet speed.

### Step 5: Generate Encryption Certificates

```bash
# Generate RSA certificates (default)
python crypto/generate_certs.py

# Or generate ECC certificates (alternative)
python crypto/generate_certs.py --ecc
```

You should see output like:
```
🔑 Generating RSA keys and certificates...
✅ User keys: user_rsa_private_key.pem, user_rsa_public_key.pem, user_rsa_certificate.pem
✅ Model keys: model_rsa_private_key.pem, model_rsa_public_key.pem, model_rsa_certificate.pem
```

### Step 6: Test Installation

#### Option A: CLI Demo (Quick Test)
```bash
# Test with lightweight model
python demo/week2_encrypted_llm_demo.py --model tinyllama --batch
```

#### Option B: Web Interface (Full Experience)
```bash
# Launch Streamlit interface
python launch_streamlit.py

# Or launch Gradio interface
python launch_gradio.py
```

## 🎮 Usage Guide

### First Time Setup in Web Interface

1. **Launch the web interface** (Streamlit or Gradio)
2. **Select a model**:
   - `tinyllama`: Ultra lightweight (1.1B parameters) - good for testing
   - `phi-3-mini`: Fast and efficient (3.8B parameters) - recommended
   - `mistral-7b`: High quality responses (7B parameters) - needs more RAM
3. **Choose encryption type**: RSA-2048 or ECC-P256
4. **Click "Initialize Encrypted LLM"**
5. **Wait for model to load** (first time takes longer due to downloads)
6. **Start chatting!**

### Understanding the Interface

#### Streamlit Interface
- **Left sidebar**: Model configuration, statistics, controls
- **Main area**: Chat interface with encrypted message history
- **Tabs**: Encryption demo, analytics, about information

#### Gradio Interface  
- **Left column**: Chat interface
- **Right sidebar**: Configuration and controls
- **Bottom**: Security information and advanced settings

### Chat Features

1. **Encrypted Messaging**: All messages are encrypted end-to-end
2. **Real-time Status**: See encryption and generation progress
3. **Message History**: View past conversations with metadata
4. **Export Chat**: Download chat history as JSON
5. **Performance Metrics**: Track generation times and statistics

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. "Module not found" errors
```bash
# Make sure you're in the project directory and virtual environment is activated
cd encrypted-llm-chat
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Check PYTHONPATH
export PYTHONPATH=.  # Linux/macOS
set PYTHONPATH=.     # Windows CMD
$env:PYTHONPATH = "." # Windows PowerShell
```

#### 2. "Certificate not found" errors
```bash
# Regenerate certificates
python crypto/generate_certs.py

# Check if certs directory exists and has .pem files
ls certs/  # Linux/macOS
dir certs\ # Windows
```

#### 3. Model loading fails / Out of memory
```bash
# Try smaller model
python demo/week2_encrypted_llm_demo.py --model tinyllama

# Check available RAM
# Windows: Task Manager > Performance > Memory
# Linux: free -h
# macOS: Activity Monitor
```

#### 4. Slow performance
- **Use GPU**: Install CUDA if you have NVIDIA GPU
- **Close other applications**: Free up RAM
- **Use smaller model**: Start with `tinyllama`
- **Reduce max response length**: In web interface settings

#### 5. Web interface won't start
```bash
# Check if ports are available
netstat -an | grep 8501  # Streamlit
netstat -an | grep 7860  # Gradio

# Try different ports
streamlit run ui/streamlit_app.py --server.port 8502
```

#### 6. Import/dependency errors
```bash
# Reinstall requirements
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Or create fresh virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Getting Help

1. **Check the logs**: Look for error messages in the terminal
2. **Verify requirements**: Ensure Python 3.10+ and all dependencies installed
3. **Test step by step**: Start with CLI demo, then web interface
4. **Check system resources**: Monitor RAM and CPU usage
5. **Try smaller model**: Use `tinyllama` for testing

## 🔧 Advanced Configuration

### Custom Model Configuration

Create `models.json`:
```json
{
  "custom_models": {
    "my-model": {
      "model_id": "microsoft/DialoGPT-medium",
      "max_memory_gb": 4,
      "quantize": true,
      "description": "Custom conversation model"
    }
  }
}
```

### Environment Variables

```bash
# Model settings
export ENCRYPTED_LLM_DEFAULT_MODEL=tinyllama
export ENCRYPTED_LLM_DEFAULT_ENCRYPTION=rsa

# Performance settings
export TORCH_NUM_THREADS=4
export OMP_NUM_THREADS=4

# Cache directory
export HF_HOME=/path/to/huggingface/cache
```

### GPU Setup (NVIDIA)

1. **Install CUDA** (if not already installed):
   - Download from [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
   - Follow installation instructions for your OS

2. **Install PyTorch with CUDA**:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Verify GPU is detected**:
   ```python
   import torch
   print(f"CUDA available: {torch.cuda.is_available()}")
   print(f"GPU count: {torch.cuda.device_count()}")
   ```

## 📱 Mobile/Remote Access

### Access from other devices on your network

1. **Find your IP address**:
   ```bash
   # Windows
   ipconfig
   
   # Linux/macOS
   ifconfig | grep inet
   ```

2. **Launch with external access**:
   ```bash
   # Streamlit
   streamlit run ui/streamlit_app.py --server.address 0.0.0.0
   
   # Gradio
   python ui/gradio_app.py  # Gradio allows external access by default
   ```

3. **Access from other devices**:
   - URL: `http://YOUR_IP_ADDRESS:8501` (Streamlit) or `http://YOUR_IP_ADDRESS:7860` (Gradio)

### Security Note
Only allow network access if you trust all devices on your network. For internet access, use proper authentication and HTTPS.

## 🎯 Quick Start Checklist

- [ ] Python 3.10+ installed
- [ ] Project downloaded/cloned
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Certificates generated (`python crypto/generate_certs.py`)
- [ ] CLI demo tested (`python demo/week2_encrypted_llm_demo.py --model tinyllama`)
- [ ] Web interface launched (`python launch_streamlit.py`)
- [ ] First encrypted chat completed

## 🎉 Success!

If you've completed all steps successfully, you now have:

✅ **Working encrypted LLM chat system**  
✅ **End-to-end encryption** with certificates  
✅ **Local AI inference** for privacy  
✅ **Modern web interface** for easy use  
✅ **Multiple model options** for different needs  

**Enjoy your private, encrypted AI conversations!** 🔐🤖

---

Need more help? Check out:
- [DEPLOYMENT.md](DEPLOYMENT.md) for advanced deployment options
- [README.md](README.md) for project overview
- Week summaries for technical details
