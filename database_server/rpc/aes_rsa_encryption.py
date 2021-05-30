from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto import Random

from base64 import b64encode, b64decode
import json

from rpc.utils import compact_json


class ServerEncryptionHandler:
    def __init__(self, rsa_strength=2048):
        self._private_rsa_key = RSA.generate(rsa_strength)
        self._nonce_hash = set()

        pub_key = self._private_rsa_key.publickey()
        self._public_rsa_key = pub_key.exportKey().decode()

    def get_public_key(self):
        return self._public_rsa_key

    def decrypt(self, b64_enc_key, b64_nonce, b64_enc_data):
        assert b64_nonce not in self._nonce_hash
        self._nonce_hash.add(b64_nonce)

        enc_data = b64decode(b64_enc_data.encode("UTF-8"))
        enc_key = b64decode(b64_enc_key.encode("UTF-8"))
        nonce = b64decode(b64_nonce.encode("UTF-8"))

        # decrypt client's encrypted AES key
        decryptor = PKCS1_OAEP.new(self._private_rsa_key)
        key = decryptor.decrypt(enc_key)

        # use decrypted AES key to decrypt data
        cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
        decrypted = str(cipher.decrypt(enc_data), encoding="UTF-8")
        return key, json.loads(decrypted)

    def encrypt(self, key, data):
        data = compact_json(data)
        cipher = AES.new(key, AES.MODE_CTR)
        enc_data = cipher.encrypt(bytes(data, encoding="UTF-8"))

        b64_enc_data = b64encode(enc_data).decode()
        b64_nonce = b64encode(cipher.nonce).decode()

        return b64_nonce, b64_enc_data


class ClientEncryptionHandler:
    def __init__(self, public_rsa_key):
        self._public_rsa_key = RSA.import_key(public_rsa_key)

    def encrypt(self, data):
        # create AES key
        # this key will be used later for decrypting the server's response
        self._key = Random.new().read(32)

        # encrypt data using AES key
        cipher = AES.new(self._key, AES.MODE_CTR)
        enc_data = cipher.encrypt(bytes(data, encoding="UTF-8"))

        # encrypt AES key using server's public RSA key
        encryptor = PKCS1_OAEP.new(self._public_rsa_key)
        enc_key = encryptor.encrypt(self._key)

        # convert to base 64 characters (so json can parse)
        b64_enc_data = b64encode(enc_data).decode()
        b64_enc_key = b64encode(enc_key).decode()
        b64_nonce = b64encode(cipher.nonce).decode()

        # return encrypted AES key, nonce value, and encrypted data
        # only the server can decrypt the encryped AES key
        # nonce is required for decryption since it works as a salt
        # nonce is used for stopping replay attacks
        return b64_enc_key, b64_nonce, b64_enc_data

    def decrypt(self, b64_nonce, b64_enc_data):
        enc_data = b64decode(b64_enc_data.encode("UTF-8"))
        nonce = b64decode(b64_nonce.encode("UTF-8"))

        cipher = AES.new(self._key, AES.MODE_CTR, nonce=nonce)
        decrypted = str(cipher.decrypt(enc_data), encoding="UTF-8")  # TODO: str(..., encoding=) change to .decode()??
        return json.loads(decrypted)

