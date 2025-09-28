#!/usr/bin/env python3
"""
Certificate Generation Script for Encrypted LLM Chat

Run this script to generate all necessary keys and certificates.
"""

import argparse
from pathlib import Path
from crypto.key_manager import KeyManager


def main():
    """Generate certificates and keys for encrypted LLM chat."""
    parser = argparse.ArgumentParser(description="Generate keys and certificates for encrypted LLM chat")
    parser.add_argument("--ecc", action="store_true", help="Use ECC instead of RSA")
    parser.add_argument("--certs-dir", default="certs", help="Directory to store certificates")
    parser.add_argument("--force", action="store_true", help="Overwrite existing certificates")
    
    args = parser.parse_args()
    
    # Initialize key manager
    key_manager = KeyManager(args.certs_dir)
    
    # Check if certificates already exist
    certs_path = Path(args.certs_dir)
    key_type = "ecc" if args.ecc else "rsa"
    
    existing_files = [
        f"user_{key_type}_private_key.pem",
        f"user_{key_type}_public_key.pem", 
        f"user_{key_type}_certificate.pem",
        f"model_{key_type}_private_key.pem",
        f"model_{key_type}_public_key.pem",
        f"model_{key_type}_certificate.pem"
    ]
    
    if not args.force and any((certs_path / f).exists() for f in existing_files):
        print(f"⚠️  {key_type.upper()} certificates already exist in {args.certs_dir}")
        print("   Use --force to overwrite existing certificates")
        return
    
    print(f"🔑 Generating {key_type.upper()} keys and certificates...")
    print(f"📁 Certificate directory: {args.certs_dir}")
    
    # Generate user keys and certificate
    print("\n👤 Generating user keys and certificate...")
    user_files = key_manager.setup_user_keys(use_ecc=args.ecc)
    print(f"   ✅ Private key: {user_files[0]}")
    print(f"   ✅ Public key: {user_files[1]}")
    print(f"   ✅ Certificate: {user_files[2]}")
    
    # Generate model keys and certificate  
    print("\n🤖 Generating model keys and certificate...")
    model_files = key_manager.setup_model_keys(use_ecc=args.ecc)
    print(f"   ✅ Private key: {model_files[0]}")
    print(f"   ✅ Public key: {model_files[1]}")
    print(f"   ✅ Certificate: {model_files[2]}")
    
    print(f"\n✨ Certificate generation complete!")
    print(f"📁 All files saved to: {certs_path.absolute()}")
    
    # Show next steps
    print("\n🚀 Next steps:")
    print("   1. Test encryption: python crypto/message_crypto.py")
    print("   2. Run demo: python demo/encrypted_chat_demo.py")
    
    # Create .gitignore for certs directory
    gitignore_path = certs_path / ".gitignore"
    if not gitignore_path.exists():
        with open(gitignore_path, 'w') as f:
            f.write("# Ignore all certificate files\n")
            f.write("*.pem\n")
            f.write("*.key\n")
            f.write("*.crt\n")
            f.write("*.cert\n")
        print(f"   📝 Created {gitignore_path} to keep certificates private")


if __name__ == "__main__":
    main()
