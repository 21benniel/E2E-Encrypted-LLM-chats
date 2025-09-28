# 🚀 Deployment Guide for Encrypted LLM Chat

This guide covers various deployment options for the Encrypted LLM Chat application.

## 📋 Prerequisites

- Python 3.10+
- 8GB+ RAM (for local LLM inference)
- GPU with 8GB+ VRAM (optional, for faster inference)
- Docker (for containerized deployment)

## 🏠 Local Development Setup

### 1. Clone and Setup
```bash
git clone <your-repo>
cd encrypted-llm-chat
pip install -r requirements.txt
```

### 2. Generate Certificates
```bash
# Generate RSA certificates
python crypto/generate_certs.py

# Or generate ECC certificates  
python crypto/generate_certs.py --ecc
```

### 3. Launch Application
```bash
# Streamlit interface
python launch_streamlit.py

# Or Gradio interface
python launch_gradio.py

# Or CLI demo
python demo/week2_encrypted_llm_demo.py --model tinyllama
```

## 🐳 Docker Deployment

### Option 1: Docker Compose (Recommended)

```bash
# Build and start Streamlit interface
docker-compose up --build

# Or start Gradio interface
docker-compose --profile gradio up --build

# Access at:
# Streamlit: http://localhost:8501
# Gradio: http://localhost:7860
```

### Option 2: Docker Build & Run

```bash
# Build image
docker build -t encrypted-llm-chat .

# Run Streamlit
docker run -p 8501:8501 -v ./certs:/app/certs encrypted-llm-chat

# Run Gradio
docker run -p 7860:7860 -v ./certs:/app/certs encrypted-llm-chat python launch_gradio.py
```

## ☁️ Cloud Deployment

### Hugging Face Spaces

1. Create a new Space on [Hugging Face](https://huggingface.co/spaces)
2. Choose "Streamlit" or "Gradio" as the SDK
3. Upload your code:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/encrypted-llm-chat
   cp -r * encrypted-llm-chat/
   cd encrypted-llm-chat
   git add .
   git commit -m "Add encrypted LLM chat"
   git push
   ```
4. Generate certificates in the Space:
   ```python
   # Add to your app startup
   import subprocess
   subprocess.run(["python", "crypto/generate_certs.py"])
   ```

### Google Cloud Platform

#### Cloud Run Deployment

1. **Prepare for Cloud Run:**
   ```bash
   # Add to Dockerfile
   ENV PORT=8080
   CMD exec streamlit run ui/streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Build and Deploy:**
   ```bash
   # Build and push to Container Registry
   gcloud builds submit --tag gcr.io/PROJECT_ID/encrypted-llm-chat

   # Deploy to Cloud Run
   gcloud run deploy encrypted-llm-chat \
     --image gcr.io/PROJECT_ID/encrypted-llm-chat \
     --platform managed \
     --region us-central1 \
     --memory 8Gi \
     --cpu 4 \
     --timeout 3600
   ```

### AWS Deployment

#### EC2 Instance

1. **Launch EC2 Instance:**
   - Instance type: `m5.2xlarge` or `g4dn.xlarge` (with GPU)
   - Storage: 50GB+ EBS volume
   - Security group: Allow ports 8501, 7860

2. **Setup on EC2:**
   ```bash
   # Install Docker
   sudo yum update -y
   sudo yum install -y docker
   sudo service docker start

   # Clone and run
   git clone <your-repo>
   cd encrypted-llm-chat
   sudo docker-compose up -d
   ```

#### ECS Fargate

1. **Create ECS Task Definition:**
   ```json
   {
     "family": "encrypted-llm-chat",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "4096",
     "memory": "8192",
     "containerDefinitions": [
       {
         "name": "encrypted-llm-chat",
         "image": "your-ecr-repo/encrypted-llm-chat:latest",
         "portMappings": [
           {
             "containerPort": 8501,
             "protocol": "tcp"
           }
         ]
       }
     ]
   }
   ```

## 🔧 Configuration Options

### Environment Variables

```bash
# Model configuration
ENCRYPTED_LLM_MODEL=tinyllama          # Default model
ENCRYPTED_LLM_ENCRYPTION=rsa           # rsa or ecc

# Server configuration  
STREAMLIT_SERVER_PORT=8501
GRADIO_SERVER_PORT=7860
PYTHONPATH=/app

# Performance tuning
TORCH_NUM_THREADS=4
OMP_NUM_THREADS=4
```

### Custom Model Configuration

Create `config.json`:
```json
{
  "models": {
    "custom-model": {
      "model_id": "your-org/your-model",
      "max_memory_gb": 6,
      "quantize": true,
      "description": "Your custom model"
    }
  },
  "default_model": "custom-model",
  "encryption": {
    "default_type": "rsa",
    "key_size": 2048
  }
}
```

## 🔒 Security Considerations

### Production Deployment

1. **Certificate Management:**
   ```bash
   # Generate production certificates with longer validity
   python crypto/generate_certs.py --days 3650
   
   # Store certificates securely (e.g., AWS Secrets Manager)
   aws secretsmanager create-secret --name encrypted-llm-certs --secret-string file://certs.json
   ```

2. **Network Security:**
   - Use HTTPS with proper SSL certificates
   - Implement rate limiting
   - Add authentication/authorization
   - Use VPC/private networks for cloud deployment

3. **Resource Limits:**
   ```yaml
   # docker-compose.yml
   services:
     encrypted-llm-streamlit:
       deploy:
         resources:
           limits:
             memory: 8G
             cpus: '4'
   ```

### Monitoring & Logging

1. **Health Checks:**
   ```python
   # Add to your app
   @st.cache_data
   def health_check():
       return {"status": "healthy", "timestamp": datetime.now()}
   ```

2. **Logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   logger = logging.getLogger(__name__)
   ```

## 📊 Performance Optimization

### Model Optimization

1. **Quantization:**
   ```python
   # Enable 4-bit quantization for memory efficiency
   quantization_config = BitsAndBytesConfig(
       load_in_4bit=True,
       bnb_4bit_compute_dtype=torch.float16
   )
   ```

2. **Caching:**
   ```bash
   # Pre-download models
   python -c "from transformers import AutoModel; AutoModel.from_pretrained('TinyLlama/TinyLlama-1.1B-Chat-v1.0')"
   ```

### Infrastructure Scaling

1. **Horizontal Scaling:**
   ```yaml
   # Kubernetes deployment
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: encrypted-llm-chat
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: encrypted-llm-chat
   ```

2. **Load Balancing:**
   ```nginx
   upstream encrypted_llm {
       server app1:8501;
       server app2:8501;
       server app3:8501;
   }
   ```

## 🚨 Troubleshooting

### Common Issues

1. **Model Loading Fails:**
   ```bash
   # Check available memory
   free -h
   
   # Use smaller model
   python demo/week2_encrypted_llm_demo.py --model tinyllama
   ```

2. **Certificate Errors:**
   ```bash
   # Regenerate certificates
   rm -rf certs/
   python crypto/generate_certs.py
   ```

3. **Port Conflicts:**
   ```bash
   # Change ports
   export STREAMLIT_SERVER_PORT=8502
   python launch_streamlit.py
   ```

### Debug Mode

```bash
# Enable debug logging
export PYTHONPATH=.
export DEBUG=1
python ui/streamlit_app.py
```

---

## 🎯 Quick Start Commands

```bash
# Local development
git clone <repo> && cd encrypted-llm-chat
pip install -r requirements.txt
python crypto/generate_certs.py
python launch_streamlit.py

# Docker deployment
docker-compose up --build

# Cloud deployment (example)
gcloud run deploy --source .
```

For more help, see the main [README.md](README.md) or open an issue on GitHub.
