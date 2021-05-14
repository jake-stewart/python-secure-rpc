# Python Secure RPC
Work in progress for uni assignment.

### Security rundown:
1. Client encrypts their data using AES.
2. Client encrypts AES key using server's public RSA key.
3. Server decrypts AES key using their private RSA key.
4. Server decrypts client's data using AES key.

Client encrypts using a nonce, which means every request sent has a unique value.
Server does not process a request if it has the same nonce as a previous request.
This stops replay attacks.

The implementation provided has authentication capabilities.
It contains a dictionary linking usernames to SHA256 hashed passwords + their salts.

### Usage
Run `server.py` on one terminal and `client.py` on another.
If you want to create your own implementation, look at the source code of `server.py` and `client.py`. It's quite simple.

**I am not a cyber security expert. Use at your own risk.**
