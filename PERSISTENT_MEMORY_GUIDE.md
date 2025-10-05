# 🔐 Persistent Memory with E2E Encryption - Implementation Guide

## 🎉 **NEW FEATURE: Encrypted Conversation Memory**

Your E2E Encrypted LLM Chat now supports **persistent conversation memory** while maintaining complete end-to-end encryption! Every conversation is stored securely and can be resumed across sessions.

## 🏗️ **Architecture Overview**

### **How It Works:**
```
User Message → Encrypt → Store in SQLite + Encrypted Files → Decrypt → LLM Context
     ↓                                                                    ↓
LLM Response ← Encrypt ← Store in SQLite + Encrypted Files ← Generate ← Enhanced Prompt
```

### **Security Model:**
- **Each conversation** has its own unique encryption key
- **Conversation keys** are derived from user's private key + conversation ID
- **All message content** is encrypted with AES-256-GCM
- **Metadata** is stored in SQLite for fast querying
- **Message files** are encrypted and stored separately

## 🔑 **Key Features**

### ✅ **Complete E2E Encryption**
- Conversation keys derived using PBKDF2 + user private key
- Each message encrypted with unique AES key
- No plaintext ever stored on disk
- Forward secrecy through ephemeral keys

### ✅ **Conversation Context**
- LLM remembers previous messages in the conversation
- Context automatically included in prompts
- Configurable context window (tokens/messages)
- Smart context truncation for long conversations

### ✅ **Persistent Storage**
- SQLite database for metadata and indexing
- Encrypted files for message content
- Automatic conversation management
- Export/import capabilities

### ✅ **Advanced Features**
- Conversation search by title/tags
- Message deduplication
- Storage statistics and monitoring
- Conversation export to JSON

## 🚀 **Quick Start**

### **1. Enable Memory in Your Code**
```python
from llm.encrypted_llm import EncryptedLLM

# Initialize with memory enabled
encrypted_llm = EncryptedLLM(
    model_name="phi-3-mini",
    key_type="rsa",
    enable_memory=True,  # Enable persistent memory
    memory_storage_dir="conversations"  # Storage directory
)

# Create a new conversation
conversation_id = encrypted_llm.create_conversation(
    title="AI Learning Session",
    tags=["learning", "ai"]
)

# Chat with context
encrypted_response = encrypted_llm.process_encrypted_prompt(
    encrypted_prompt,
    conversation_id=conversation_id,  # Enables context
    use_context=True
)
```

### **2. Run the Demo**
```bash
# Full demo with conversation memory
python demo/persistent_memory_demo.py

# Interactive chat with memory
python demo/persistent_memory_demo.py
# Choose option 3 for interactive demo
```

### **3. Manage Conversations**
```bash
# List all conversations
python conversation_manager.py list

# View specific conversation
python conversation_manager.py view conv_1234567890_abcd1234

# Search conversations
python conversation_manager.py search "machine learning"

# Export conversation
python conversation_manager.py export conv_1234567890_abcd1234

# Show storage statistics
python conversation_manager.py stats
```

## 📊 **Storage Structure**

### **Directory Layout:**
```
conversations/
├── conversations.db          # SQLite metadata database
├── conv_123_msg_456.enc     # Encrypted message files
├── conv_123_msg_789.enc
└── conv_456_msg_101.enc
```

### **Database Schema:**
```sql
-- Conversation metadata
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    model_name TEXT,
    encryption_type TEXT,
    tags TEXT,  -- JSON array
    total_tokens INTEGER DEFAULT 0,
    encrypted_key TEXT NOT NULL,  -- Conversation key encrypted with user key
    salt TEXT NOT NULL
);

-- Message index for fast queries
CREATE TABLE message_index (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,
    timestamp TEXT,
    content_hash TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
);
```

## 🔐 **Encryption Details**

### **Key Derivation Process:**
```python
# 1. Generate unique salt for conversation
salt = os.urandom(32)

# 2. Derive conversation key from user key + conversation ID
user_key_bytes = user_private_key.private_bytes(...)
kdf_input = user_key_bytes + conversation_id.encode('utf-8')

# 3. Apply PBKDF2 with 100,000 iterations
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
conversation_key = kdf.derive(kdf_input)

# 4. Encrypt conversation key with user's public key for storage
encrypted_conv_key = rsa_encrypt(conversation_key, user_public_key)
```

### **Message Encryption:**
```python
# Each message encrypted with AES-256-GCM
def encrypt_message(content, conversation_key):
    iv = os.urandom(12)  # 96-bit IV
    cipher = Cipher(algorithms.AES(conversation_key), modes.GCM(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(content.encode()) + encryptor.finalize()
    
    return {
        'ciphertext': base64.b64encode(ciphertext).decode(),
        'iv': base64.b64encode(iv).decode(),
        'tag': base64.b64encode(encryptor.tag).decode()
    }
```

## 🧠 **Context Management**

### **How Context Works:**
1. **Message Storage**: Each message stored with timestamp and metadata
2. **Context Retrieval**: Recent messages loaded based on token/message limits
3. **Prompt Enhancement**: Context prepended to current user message
4. **Smart Truncation**: Older messages removed if context exceeds limits

### **Context Format:**
```
Previous conversation:
Human: What is machine learning?
Assistant: Machine learning is a subset of AI that enables computers to learn...
