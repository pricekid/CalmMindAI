"""
Generate VAPID Keys for Push Notifications

This script generates the necessary VAPID keys for web push notifications.
Run this script once during initial setup to create your keys.

Usage:
    python generate_vapid_keys.py

The keys will be displayed in the console. You should set these as environment
variables VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY in your application.
"""

import base64
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def generate_keys():
    """Generate VAPID keys for web push notifications."""
    try:
        # Using Python's built-in cryptography tools
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        
        # Generate a new ECDSA key pair for VAPID
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        # Get public key in the right format
        public_key_raw = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        
        # Get private key in the right format
        private_key_raw = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Convert to URL-safe base64 encoding
        public_key = base64.urlsafe_b64encode(public_key_raw).decode('utf-8')
        private_key = private_key_raw.decode('utf-8')
        
        return {
            "public_key": public_key,
            "private_key": private_key
        }
    except ImportError:
        logger.error("Required cryptography module not found. Run 'pip install cryptography' to install it.")
        return None
    except Exception as e:
        logger.error(f"Error generating VAPID keys: {e}")
        return None

def main():
    """Main function to generate and display VAPID keys."""
    logger.info("Generating VAPID keys for web push notifications...")
    
    keys = generate_keys()
    if not keys:
        logger.error("Failed to generate VAPID keys")
        sys.exit(1)
    
    print("\n=========== VAPID KEYS ===========")
    print("These keys are used for web push notifications.")
    print("Add them to your environment variables:\n")
    
    print(f"VAPID_PUBLIC_KEY={keys['public_key']}")
    print(f"VAPID_PRIVATE_KEY={keys['private_key']}")
    
    print("\n==================================")
    print("Keep your private key secure and never share it publicly.")
    print("The public key can be shared with the browser clients.")
    
    logger.info("VAPID keys generated successfully")

if __name__ == "__main__":
    main()