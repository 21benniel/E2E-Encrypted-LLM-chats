#!/usr/bin/env python3
"""
Conversation Management Utility

Command-line tool for managing encrypted conversations.
Allows listing, viewing, searching, and exporting conversations.
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from crypto.conversation_memory import EncryptedConversationMemory
    MEMORY_AVAILABLE = True
except ImportError as e:
    MEMORY_AVAILABLE = False
    print(f"Memory system not available: {e}")


def list_conversations(memory: EncryptedConversationMemory, limit: int = 20):
    """List conversations."""
    print(f"📋 Recent Conversations (limit: {limit})")
    print("=" * 60)
    
    conversations = memory.list_conversations(limit)
    
    if not conversations:
        print("No conversations found.")
        return
    
    for i, conv in enumerate(conversations, 1):
        print(f"{i:2d}. {conv.title}")
        print(f"    ID: {conv.conversation_id}")
        print(f"    Messages: {conv.message_count}")
        print(f"    Model: {conv.model_name}")
        print(f"    Updated: {conv.last_updated}")
        print(f"    Tags: {', '.join(conv.tags) if conv.tags else 'None'}")
        print()


def view_conversation(memory: EncryptedConversationMemory, conversation_id: str):
    """View conversation messages."""
    print(f"📖 Conversation: {conversation_id}")
    print("=" * 60)
    
    # Get metadata
    metadata = memory.get_conversation_metadata(conversation_id)
    if not metadata:
        print(f"❌ Conversation not found: {conversation_id}")
        return
    
    print(f"Title: {metadata.title}")
    print(f"Created: {metadata.created_at}")
    print(f"Messages: {metadata.message_count}")
    print(f"Model: {metadata.model_name}")
    print(f"Tags: {', '.join(metadata.tags) if metadata.tags else 'None'}")
    print()
    
    # Get messages
    messages = memory.get_conversation_messages(conversation_id)
    
    if not messages:
        print("No messages found.")
        return
    
    for i, msg in enumerate(messages, 1):
        role_icon = "👤" if msg.role == "user" else "🤖"
        print(f"{i:2d}. {role_icon} {msg.role.title()}: {msg.content}")
        print(f"    Time: {msg.timestamp}")
        if msg.metadata:
            print(f"    Metadata: {json.dumps(msg.metadata, indent=8)}")
        print()


def search_conversations(memory: EncryptedConversationMemory, query: str):
    """Search conversations."""
    print(f"🔍 Search Results for: '{query}'")
    print("=" * 60)
    
    results = memory.search_conversations(query)
    
    if not results:
        print("No conversations found matching the query.")
        return
    
    for i, conv in enumerate(results, 1):
        print(f"{i}. {conv.title}")
        print(f"   ID: {conv.conversation_id}")
        print(f"   Messages: {conv.message_count}")
        print(f"   Updated: {conv.last_updated}")
        print()


def export_conversation(memory: EncryptedConversationMemory, conversation_id: str, output_file: str = None):
    """Export conversation to JSON."""
    print(f"📤 Exporting conversation: {conversation_id}")
    
    try:
        export_data = memory.export_conversation(conversation_id)
        
        if not export_data:
            print(f"❌ Conversation not found: {conversation_id}")
            return
        
        # Generate filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"conversation_export_{timestamp}.json"
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Conversation exported to: {output_file}")
        print(f"   Messages: {len(export_data['messages'])}")
        print(f"   Size: {Path(output_file).stat().st_size} bytes")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")


def delete_conversation(memory: EncryptedConversationMemory, conversation_id: str, confirm: bool = False):
    """Delete a conversation."""
    if not confirm:
        # Get conversation info first
        metadata = memory.get_conversation_metadata(conversation_id)
        if not metadata:
            print(f"❌ Conversation not found: {conversation_id}")
            return
        
        print(f"⚠️  About to delete conversation:")
        print(f"   Title: {metadata.title}")
        print(f"   Messages: {metadata.message_count}")
        print(f"   Created: {metadata.created_at}")
        
        confirm_input = input("Are you sure? (yes/no): ").strip().lower()
        if confirm_input not in ['yes', 'y']:
            print("❌ Deletion cancelled.")
            return
    
    print(f"🗑️  Deleting conversation: {conversation_id}")
    
    if memory.delete_conversation(conversation_id):
        print("✅ Conversation deleted successfully.")
    else:
        print("❌ Failed to delete conversation.")


def show_stats(memory: EncryptedConversationMemory):
    """Show storage statistics."""
    print("📊 Storage Statistics")
    print("=" * 30)
    
    stats = memory.get_storage_stats()
    
    print(f"Conversations: {stats['conversations']}")
    print(f"Messages: {stats['messages']}")
    print(f"Total Tokens: {stats['total_tokens']:,}")
    print(f"Storage Size: {stats['storage_size_mb']} MB")
    print(f"Storage Directory: {stats['storage_directory']}")


def main():
    """Main CLI function."""
    if not MEMORY_AVAILABLE:
        print("❌ Memory system not available. Please check your installation.")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="Encrypted Conversation Management Utility")
    parser.add_argument("--storage-dir", default="conversations", help="Conversation storage directory")
    parser.add_argument("--user-key", default="certs/user_rsa_private_key.pem", help="User private key file")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List conversations")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum number of conversations to show")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View conversation messages")
    view_parser.add_argument("conversation_id", help="Conversation ID to view")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search conversations")
    search_parser.add_argument("query", help="Search query")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export conversation to JSON")
    export_parser.add_argument("conversation_id", help="Conversation ID to export")
    export_parser.add_argument("--output", help="Output file path")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete conversation")
    delete_parser.add_argument("conversation_id", help="Conversation ID to delete")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show storage statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize memory system
    try:
        memory = EncryptedConversationMemory(
            storage_dir=args.storage_dir,
            user_key_file=args.user_key
        )
    except Exception as e:
        print(f"❌ Failed to initialize memory system: {e}")
        print(f"   Make sure the user key exists: {args.user_key}")
        sys.exit(1)
    
    # Execute command
    try:
        if args.command == "list":
            list_conversations(memory, args.limit)
        
        elif args.command == "view":
            view_conversation(memory, args.conversation_id)
        
        elif args.command == "search":
            search_conversations(memory, args.query)
        
        elif args.command == "export":
            export_conversation(memory, args.conversation_id, args.output)
        
        elif args.command == "delete":
            delete_conversation(memory, args.conversation_id, args.force)
        
        elif args.command == "stats":
            show_stats(memory)
        
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
