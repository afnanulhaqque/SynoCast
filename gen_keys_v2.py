import os
# Create a DER encoded private key
# Using cryptography if available, or just a shell command via python
# Actually, pywebpush has a CLI. Let's try running the module.

import subprocess
import sys

# Subprocess block removed

# Since we just want keys, we can use ecdsa library if installed, or just 'openssl' if available. 
# But let's assume the user might not have openssl in path on Windows. 
# Best bet: check if 'pywebpush' installed a script in Scripts/vapid.exe

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import base64
import json

def int_to_bytes(i, length):
    return i.to_bytes(length, 'big')

def create_vapid_keys():
    # Helper to generate keys compatible with VAPID
    curve = ec.SECP256R1()
    private_key = ec.generate_private_key(curve)
    public_key = private_key.public_key()

    # Serialize Private Key
    private_val = private_key.private_numbers().private_value
    private_bytes = int_to_bytes(private_val, 32)
    private_b64 = base64.urlsafe_b64encode(private_bytes).decode('utf-8').strip('=')

    # Serialize Public Key (Uncompressed format)
    public_nums = public_key.public_numbers()
    x = int_to_bytes(public_nums.x, 32)
    y = int_to_bytes(public_nums.y, 32)
    # 0x04 is the prefix for uncompressed keys
    public_bytes = b'\x04' + x + y
    public_b64 = base64.urlsafe_b64encode(public_bytes).decode('utf-8').strip('=')

    print(f"VAPID_PRIVATE_KEY={private_b64}")
    print(f"VAPID_PUBLIC_KEY={public_b64}")

if __name__ == "__main__":
    try:
        create_vapid_keys()
    except ImportError:
        print("Cryptography not found, trying minimal generation or failure.")
