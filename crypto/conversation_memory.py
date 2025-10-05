"""
Encrypted Conversation Memory Module

Provides persistent, encrypted storage for conversation history while maintaining E2E encryption.
Each conversation is encrypted with its own unique key derived from user credentials.
"""

import os
import json
import time
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa, ec

from .message_crypto import MessageCrypto


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    metadata: Dict[str, Any]
    message_id: str
    encryption_info: Dict[str, str]


@dataclass
class ConversationMetadata:
    """Metadata for a conversation."""
    conversation_id: str
    title: str
    created_at: str
    last_updated: str
    message_count: int
    model_name: str
    encryption_type: str
    tags: List[str]
    total_tokens: int


class EncryptedConversationMemory:
    """
    Manages encrypted persistent storage of conversations.
    
    Features:
    - Each conversation encrypted with unique derived key
    - Metadata stored separately from content
    - Support for conversation search and management
    - Automatic key derivation from user credentials
    - SQLite backend for efficient querying
    """
    
    def __init__(
        self, 
        storage_dir: str = "conversations",
        user_key_file: str = "certs/user_rsa_private_key.pem",
        db_name: str = "conversations.db"
    ):
        """Initialize encrypted conversation memory."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.db_path = self.storage_dir / db_name
        self.crypto = MessageCrypto()
        
        # Load user key for conversation key derivation
        self._load_user_key(user_key_file)
        
        # Initialize database
        self._init_database()
        
        print(f"✅ Encrypted conversation memory initialized at {self.storage_dir}")
    
    def _load_user_key(self, key_file: str):
        """Load user private key for key derivation."""
        try:
            with open(key_file, 'rb') as f:
                self.user_private_key = serialization.load_pem_private_key(
                    f.read(), 
                    password=None
                )
            print("✅ Loaded user key for conversation encryption")
        except FileNotFoundError:
            raise FileNotFoundError(f"User key not found: {key_file}")
    
    def _init_database(self):
        """Initialize SQLite database for conversation metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
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
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS message_index (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    role TEXT,
                    timestamp TEXT,
                    content_hash TEXT,  -- For deduplication
                    FOREIGN KEY (conversation_id) REFERENCES conversations (conversation_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_updated 
                ON conversations (last_updated DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_message_conversation 
                ON message_index (conversation_id, timestamp)
            """)
    
    def _derive_conversation_key(self, conversation_id: str, salt: bytes) -> bytes:
        """Derive unique encryption key for a conversation."""
        # Use user private key + conversation ID to derive unique key
        user_key_bytes = self.user_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Create key derivation input
        kdf_input = user_key_bytes + conversation_id.encode('utf-8')
        
        # Derive 256-bit key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        return kdf.derive(kdf_input)
    
    def _encrypt_conversation_data(self, data: str, conversation_key: bytes) -> Dict[str, str]:
        """Encrypt conversation data using AES-GCM."""
        return self.crypto._encrypt_aes(data.encode('utf-8'), conversation_key)
    
    def _decrypt_conversation_data(self, encrypted_data: Dict[str, str], conversation_key: bytes) -> str:
        """Decrypt conversation data using AES-GCM."""
        decrypted_bytes = self.crypto._decrypt_aes(encrypted_data, conversation_key)
        return decrypted_bytes.decode('utf-8')
    
    def create_conversation(
        self, 
        title: str = None, 
        model_name: str = "unknown",
        encryption_type: str = "rsa",
        tags: List[str] = None
    ) -> str:
        """Create a new encrypted conversation."""
        conversation_id = f"conv_{int(time.time())}_{hashlib.md5(os.urandom(16)).hexdigest()[:8]}"
        
        if title is None:
            title = f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Generate unique salt for this conversation
        salt = os.urandom(32)
        
        # Derive conversation encryption key
        conversation_key = self._derive_conversation_key(conversation_id, salt)
        
        # Encrypt the conversation key with user's public key for storage
        encrypted_conv_key = self.crypto._encrypt_key_rsa(
            conversation_key, 
            self.user_private_key.public_key()
        )
        
        # Create conversation metadata
        metadata = ConversationMetadata(
            conversation_id=conversation_id,
            title=title,
            created_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            message_count=0,
            model_name=model_name,
            encryption_type=encryption_type,
            tags=tags or [],
            total_tokens=0
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversations 
                (conversation_id, title, created_at, last_updated, message_count, 
                 model_name, encryption_type, tags, total_tokens, encrypted_key, salt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conversation_id, title, metadata.created_at, metadata.last_updated,
                0, model_name, encryption_type, json.dumps(tags or []), 0,
                encrypted_conv_key, salt.hex()
            ))
        
        print(f"✅ Created encrypted conversation: {conversation_id}")
        return conversation_id
    
    def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str, 
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add an encrypted message to a conversation."""
        # Generate message ID
        message_id = f"msg_{int(time.time())}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        # Get conversation key
        conversation_key = self._get_conversation_key(conversation_id)
        if not conversation_key:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        # Create message object
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            message_id=message_id,
            encryption_info={
                "algorithm": "AES-256-GCM",
                "key_derivation": "PBKDF2-SHA256"
            }
        )
        
        # Encrypt message content
        message_json = json.dumps(asdict(message), indent=2)
        encrypted_message = self._encrypt_conversation_data(message_json, conversation_key)
        
        # Store encrypted message to file
        message_file = self.storage_dir / f"{conversation_id}_{message_id}.enc"
        with open(message_file, 'w') as f:
            json.dump(encrypted_message, f)
        
        # Update message index
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        with sqlite3.connect(self.db_path) as conn:
            # Add to message index
            conn.execute("""
                INSERT INTO message_index 
                (message_id, conversation_id, role, timestamp, content_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (message_id, conversation_id, role, message.timestamp, content_hash))
            
            # Update conversation metadata
            conn.execute("""
                UPDATE conversations 
                SET last_updated = ?, message_count = message_count + 1,
                    total_tokens = total_tokens + ?
                WHERE conversation_id = ?
            """, (datetime.now().isoformat(), len(content.split()), conversation_id))
        
        print(f"✅ Added encrypted message to {conversation_id}")
        return message_id
    
    def get_conversation_messages(
        self, 
        conversation_id: str, 
        limit: int = None,
        offset: int = 0
    ) -> List[ConversationMessage]:
        """Retrieve and decrypt messages from a conversation."""
        conversation_key = self._get_conversation_key(conversation_id)
        if not conversation_key:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        # Get message IDs from index
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT message_id FROM message_index 
                WHERE conversation_id = ? 
                ORDER BY timestamp ASC
            """
            params = [conversation_id]
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor = conn.execute(query, params)
            message_ids = [row[0] for row in cursor.fetchall()]
        
        # Load and decrypt messages
        messages = []
        for message_id in message_ids:
            message_file = self.storage_dir / f"{conversation_id}_{message_id}.enc"
            
            if message_file.exists():
                try:
                    with open(message_file, 'r') as f:
                        encrypted_data = json.load(f)
                    
                    # Decrypt message
                    decrypted_json = self._decrypt_conversation_data(encrypted_data, conversation_key)
                    message_dict = json.loads(decrypted_json)
                    
                    # Convert to ConversationMessage object
                    message = ConversationMessage(**message_dict)
                    messages.append(message)
                    
                except Exception as e:
                    print(f"⚠️  Failed to decrypt message {message_id}: {e}")
                    continue
        
        return messages
    
    def _get_conversation_key(self, conversation_id: str) -> Optional[bytes]:
        """Retrieve and decrypt the conversation key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT encrypted_key, salt FROM conversations 
                WHERE conversation_id = ?
            """, (conversation_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            encrypted_key, salt_hex = result
            salt = bytes.fromhex(salt_hex)
            
            # Decrypt conversation key
            conversation_key = self.crypto._decrypt_key_rsa(
                encrypted_key, 
                self.user_private_key
            )
            
            return conversation_key
    
    def get_conversation_metadata(self, conversation_id: str) -> Optional[ConversationMetadata]:
        """Get conversation metadata."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT conversation_id, title, created_at, last_updated, message_count,
                       model_name, encryption_type, tags, total_tokens
                FROM conversations WHERE conversation_id = ?
            """, (conversation_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            return ConversationMetadata(
                conversation_id=result[0],
                title=result[1],
                created_at=result[2],
                last_updated=result[3],
                message_count=result[4],
                model_name=result[5],
                encryption_type=result[6],
                tags=json.loads(result[7]) if result[7] else [],
                total_tokens=result[8]
            )
    
    def list_conversations(self, limit: int = 50) -> List[ConversationMetadata]:
        """List all conversations ordered by last updated."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT conversation_id, title, created_at, last_updated, message_count,
                       model_name, encryption_type, tags, total_tokens
                FROM conversations 
                ORDER BY last_updated DESC 
                LIMIT ?
            """, (limit,))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append(ConversationMetadata(
                    conversation_id=row[0],
                    title=row[1],
                    created_at=row[2],
                    last_updated=row[3],
                    message_count=row[4],
                    model_name=row[5],
                    encryption_type=row[6],
                    tags=json.loads(row[7]) if row[7] else [],
                    total_tokens=row[8]
                ))
            
            return conversations
    
    def get_conversation_context(
        self, 
        conversation_id: str, 
        max_messages: int = 10,
        max_tokens: int = 2048
    ) -> str:
        """Get recent conversation context for LLM prompt."""
        messages = self.get_conversation_messages(conversation_id, limit=max_messages)
        
        if not messages:
            return ""
        
        # Build context string
        context_parts = []
        token_count = 0
        
        # Start from most recent and work backwards
        for message in reversed(messages):
            message_tokens = len(message.content.split())
            
            if token_count + message_tokens > max_tokens:
                break
            
            role_prefix = "Human" if message.role == "user" else "Assistant"
            context_parts.insert(0, f"{role_prefix}: {message.content}")
            token_count += message_tokens
        
        return "\n\n".join(context_parts)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        try:
            # Get all message IDs
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT message_id FROM message_index 
                    WHERE conversation_id = ?
                """, (conversation_id,))
                message_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete from database
                conn.execute("DELETE FROM message_index WHERE conversation_id = ?", (conversation_id,))
                conn.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
            
            # Delete encrypted message files
            for message_id in message_ids:
                message_file = self.storage_dir / f"{conversation_id}_{message_id}.enc"
                if message_file.exists():
                    message_file.unlink()
            
            print(f"✅ Deleted conversation: {conversation_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete conversation {conversation_id}: {e}")
            return False
    
    def search_conversations(self, query: str, limit: int = 10) -> List[ConversationMetadata]:
        """Search conversations by title or tags."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT conversation_id, title, created_at, last_updated, message_count,
                       model_name, encryption_type, tags, total_tokens
                FROM conversations 
                WHERE title LIKE ? OR tags LIKE ?
                ORDER BY last_updated DESC 
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            
            conversations = []
            for row in cursor.fetchall():
                conversations.append(ConversationMetadata(
                    conversation_id=row[0],
                    title=row[1],
                    created_at=row[2],
                    last_updated=row[3],
                    message_count=row[4],
                    model_name=row[5],
                    encryption_type=row[6],
                    tags=json.loads(row[7]) if row[7] else [],
                    total_tokens=row[8]
                ))
            
            return conversations
    
    def export_conversation(self, conversation_id: str, include_metadata: bool = True) -> Dict[str, Any]:
        """Export a conversation in JSON format (decrypted)."""
        metadata = self.get_conversation_metadata(conversation_id)
        messages = self.get_conversation_messages(conversation_id)
        
        if not metadata:
            raise ValueError(f"Conversation not found: {conversation_id}")
        
        export_data = {
            "conversation_id": conversation_id,
            "export_timestamp": datetime.now().isoformat(),
            "messages": [asdict(msg) for msg in messages]
        }
        
        if include_metadata:
            export_data["metadata"] = asdict(metadata)
        
        return export_data
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Get conversation count
            cursor = conn.execute("SELECT COUNT(*) FROM conversations")
            conv_count = cursor.fetchone()[0]
            
            # Get total messages
            cursor = conn.execute("SELECT COUNT(*) FROM message_index")
            msg_count = cursor.fetchone()[0]
            
            # Get total tokens
            cursor = conn.execute("SELECT SUM(total_tokens) FROM conversations")
            total_tokens = cursor.fetchone()[0] or 0
        
        # Get storage size
        storage_size = sum(f.stat().st_size for f in self.storage_dir.rglob('*') if f.is_file())
        
        return {
            "conversations": conv_count,
            "messages": msg_count,
            "total_tokens": total_tokens,
            "storage_size_bytes": storage_size,
            "storage_size_mb": round(storage_size / (1024 * 1024), 2),
            "storage_directory": str(self.storage_dir)
        }


def main():
    """Demo the encrypted conversation memory."""
    print("🔐 Encrypted Conversation Memory Demo")
    print("=" * 50)
    
    try:
        # Initialize memory system
        memory = EncryptedConversationMemory()
        
        # Create a test conversation
        conv_id = memory.create_conversation(
            title="Test Encrypted Chat",
            model_name="phi-3-mini",
            tags=["test", "demo"]
        )
        
        # Add some messages
        memory.add_message(conv_id, "user", "Hello, can you help me with encryption?")
        memory.add_message(conv_id, "assistant", "Of course! I'd be happy to help you understand encryption concepts.")
        memory.add_message(conv_id, "user", "What's the difference between symmetric and asymmetric encryption?")
        memory.add_message(conv_id, "assistant", "Great question! Symmetric encryption uses the same key for both encryption and decryption, while asymmetric encryption uses a pair of keys...")
        
        # Retrieve conversation
        print(f"\n📖 Retrieving conversation: {conv_id}")
        messages = memory.get_conversation_messages(conv_id)
        
        for msg in messages:
            print(f"{msg.role.upper()}: {msg.content}")
            print(f"  Time: {msg.timestamp}")
            print()
        
        # Get context for LLM
        context = memory.get_conversation_context(conv_id)
        print("🧠 Context for LLM:")
        print(context)
        
        # Show statistics
        stats = memory.get_storage_stats()
        print(f"\n📊 Storage Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # List conversations
        conversations = memory.list_conversations()
        print(f"\n📋 All Conversations:")
        for conv in conversations:
            print(f"  {conv.title} ({conv.message_count} messages)")
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
