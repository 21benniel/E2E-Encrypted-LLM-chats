"""
LLM Model Manager for Encrypted LLM Chat

Handles loading and inference of local LLMs (Phi-3, Mistral, etc.)
Optimized for 8GB VRAM systems with quantization support.
"""

import os
import gc
import torch
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from transformers import (
        AutoTokenizer, AutoModelForCausalLM, 
        BitsAndBytesConfig, pipeline
    )
    from accelerate import infer_auto_device_map
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️  Transformers not available. Install with: pip install transformers torch accelerate")


class ModelManager:
    """Manages local LLM loading and inference with memory optimization."""
    
    # Model configurations optimized for 8GB VRAM
    SUPPORTED_MODELS = {
        "phi-3-mini": {
            "model_id": "microsoft/Phi-3-mini-4k-instruct",
            "max_memory_gb": 4,
            "quantize": True,
            "description": "Microsoft Phi-3 Mini (3.8B) - Fast and efficient"
        },
        "mistral-7b": {
            "model_id": "mistralai/Mistral-7B-Instruct-v0.3",
            "max_memory_gb": 6,
            "quantize": True,
            "description": "Mistral 7B - High quality responses"
        },
        "phi-3-mini-128k": {
            "model_id": "microsoft/Phi-3-mini-128k-instruct",
            "max_memory_gb": 4,
            "quantize": True,
            "description": "Phi-3 Mini with 128k context length"
        },
        "tinyllama": {
            "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "max_memory_gb": 2,
            "quantize": False,
            "description": "TinyLlama 1.1B - Ultra lightweight for testing"
        }
    }
    
    def __init__(self, model_name: str = "phi-3-mini", cache_dir: Optional[str] = None):
        """
        Initialize ModelManager.
        
        Args:
            model_name: Name of the model to use (from SUPPORTED_MODELS)
            cache_dir: Directory to cache downloaded models
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("Transformers library is required. Install with: pip install transformers torch accelerate")
        
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "encrypted_llm_chat"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model_name}. Choose from: {list(self.SUPPORTED_MODELS.keys())}")
        
        self.model_config = self.SUPPORTED_MODELS[model_name]
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        # Check system capabilities
        self._check_system_requirements()
    
    def _check_system_requirements(self):
        """Check if system meets requirements for the selected model."""
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
            required_memory = self.model_config["max_memory_gb"]
            
            print(f"🔍 GPU Memory: {gpu_memory:.1f}GB available, {required_memory}GB required")
            
            if gpu_memory < required_memory:
                print(f"⚠️  Warning: GPU memory might be insufficient. Consider using quantization.")
        else:
            print("⚠️  CUDA not available. Model will run on CPU (slower).")
    
    def load_model(self, force_reload: bool = False) -> bool:
        """
        Load the selected model with optimizations.
        
        Args:
            force_reload: Force reload even if model is already loaded
            
        Returns:
            True if successful, False otherwise
        """
        if self.model is not None and not force_reload:
            print(f"✅ Model {self.model_name} already loaded")
            return True
        
        try:
            model_id = self.model_config["model_id"]
            print(f"🔄 Loading {self.model_name} ({model_id})...")
            
            # Configure quantization if needed
            quantization_config = None
            if self.model_config["quantize"] and torch.cuda.is_available():
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
                print("🔧 Using 4-bit quantization for memory efficiency")
            
            # Load tokenizer
            print("📝 Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # Ensure pad token exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model
            print("🧠 Loading model...")
            device_map = "auto" if torch.cuda.is_available() else "cpu"
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                cache_dir=self.cache_dir,
                quantization_config=quantization_config,
                device_map=device_map,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
            
            # Create pipeline for easier inference
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map=device_map,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            print(f"✅ Successfully loaded {self.model_name}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load model {self.model_name}: {e}")
            return False
    
    def generate_response(
        self, 
        prompt: str, 
        max_length: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True
    ) -> str:
        """
        Generate a response to the given prompt.
        
        Args:
            prompt: Input prompt
            max_length: Maximum response length
            temperature: Sampling temperature (0.0 = deterministic)
            top_p: Top-p sampling parameter
            do_sample: Whether to use sampling
            
        Returns:
            Generated response text
        """
        if self.pipeline is None:
            if not self.load_model():
                return "❌ Error: Model not loaded"
        
        try:
            # Format prompt based on model type
            formatted_prompt = self._format_prompt(prompt)
            
            # Generate response
            outputs = self.pipeline(
                formatted_prompt,
                max_new_tokens=max_length,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.eos_token_id,
                return_full_text=False  # Only return new tokens
            )
            
            response = outputs[0]['generated_text'].strip()
            
            # Clean up response
            response = self._clean_response(response)
            
            return response
            
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return f"❌ Error generating response: {str(e)}"
    
    def _format_prompt(self, prompt: str) -> str:
        """Format prompt according to model's expected format."""
        if "phi-3" in self.model_name.lower():
            # Phi-3 chat format
            return f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"
        elif "mistral" in self.model_name.lower():
            # Mistral instruct format
            return f"[INST] {prompt} [/INST]"
        elif "tinyllama" in self.model_name.lower():
            # TinyLlama chat format
            return f"<|system|>\nYou are a helpful assistant.</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
        else:
            # Generic format
            return f"User: {prompt}\nAssistant:"
    
    def _clean_response(self, response: str) -> str:
        """Clean up model response."""
        # Remove common artifacts
        response = response.replace("<|end|>", "")
        response = response.replace("</s>", "")
        response = response.replace("<|assistant|>", "")
        
        # Split on common stop patterns and take first part
        stop_patterns = ["\nUser:", "\n<|user|>", "\n[INST]", "\n---"]
        for pattern in stop_patterns:
            if pattern in response:
                response = response.split(pattern)[0]
        
        return response.strip()
    
    def unload_model(self):
        """Unload model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.tokenizer is not None:
            del self.tokenizer  
            self.tokenizer = None
            
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
        
        # Force garbage collection
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print(f"🗑️  Unloaded {self.model_name}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        config = self.model_config.copy()
        config["loaded"] = self.model is not None
        config["model_name"] = self.model_name
        
        if torch.cuda.is_available():
            config["gpu_available"] = True
            config["gpu_memory_gb"] = torch.cuda.get_device_properties(0).total_memory / 1024**3
        else:
            config["gpu_available"] = False
            config["gpu_memory_gb"] = 0
        
        return config
    
    @classmethod
    def list_supported_models(cls) -> Dict[str, str]:
        """List all supported models with descriptions."""
        return {name: config["description"] for name, config in cls.SUPPORTED_MODELS.items()}


def main():
    """Demo model loading and inference."""
    print("🔧 LLM Model Manager Demo")
    print("=" * 40)
    
    # List available models
    print("📋 Supported models:")
    for name, desc in ModelManager.list_supported_models().items():
        print(f"  • {name}: {desc}")
    
    # Choose model (default to smallest for demo)
    model_name = "tinyllama"  # Start with smallest model
    print(f"\n🚀 Testing with {model_name}")
    
    # Initialize manager
    manager = ModelManager(model_name)
    
    # Show model info
    info = manager.get_model_info()
    print(f"\n📊 Model info:")
    for key, value in info.items():
        print(f"  • {key}: {value}")
    
    # Load model
    if manager.load_model():
        # Test inference
        test_prompts = [
            "Hello, how are you?",
            "What is artificial intelligence?",
            "Explain encryption in simple terms."
        ]
        
        print(f"\n🧪 Testing inference:")
        for prompt in test_prompts:
            print(f"\n👤 Prompt: {prompt}")
            response = manager.generate_response(prompt, max_length=100)
            print(f"🤖 Response: {response}")
        
        # Unload model
        manager.unload_model()
    else:
        print("❌ Failed to load model for testing")


if __name__ == "__main__":
    main()
