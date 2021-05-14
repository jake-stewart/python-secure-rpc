#!/usr/bin/python3

import json
from utils import compact_json

import socket
import traceback
import threading

try:
    from AES_RSA_encryption import ServerEncryptionHandler
    HAS_ENCRYPTION = 1
except:
    print("WARNING: NO ENCRYPTION LIBRARY INSTALLED")
    print("Install Pycryptodome before handling confidential information.")
    HAS_ENCRYPTION = 0

# error codes
INVALID_HOOK = 1
RPC_EXCEPTION = 2
CRITICAL_ERROR = 3


class Server:
    def __init__(self, host='', port=8080):
        self._host = host
        self._port = port
        self._active = False
        self._hooks = {"connect": self._handle_new_connection}
        if HAS_ENCRYPTION:
            self._encryption_handler = ServerEncryptionHandler()
        else:
            self._encryption_handler = None

    def add_hook(self, target):
        self._hooks[target.__name__] = target

    def remove_hook(self, target):
        del self._hooks[target.__name__]

    def shutdown(self):
        self._active = False
        self._socket.close()

    def start(self):
        self._active = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._host, self._port))
        self._socket.listen()

        while self._active:
            connection, _ = self._socket.accept()

            threading.Thread(
                target=self._connection_handler,
                args=(connection,), daemon=True
            ).start()

    def _handle_new_connection(self, client_has_encryption):
        if HAS_ENCRYPTION and client_has_encryption:
            return [1, self._encryption_handler.get_secret()]
        else:
            return [0, None]

    def _connection_handler(self, connection):
        hook_processed = False
        try:
            # recieve request
            encrypted, *enc_args, request = self._recv(connection)

            # remove encryption
            enc_args, request = self._remove_encryption_layer(encrypted, enc_args, request)
            hook, args, kwargs = request

            # execute RPC
            response = self._handle_request(hook, args, kwargs)
            hook_processed = True

            # encrypt output
            encryption_layer = self._add_encryption_layer(encrypted, enc_args, response)

        except:
            encryption_layer = [0, [CRITICAL_ERROR, hook_processed]]
            print("CRITICAL ERROR:\n" + traceback.format_exc())

        # send response
        self._send(connection, encryption_layer)

    def _remove_encryption_layer(self, encrypted, enc_args, request):
        if encrypted:
            *enc_args, request = self._encryption_handler.decrypt(
                *enc_args, request
            )
        return enc_args, request

    def _add_encryption_layer(self, encrypted, enc_args, response):
        if encrypted:
            return [1, *self._encryption_handler.encrypt(*enc_args, response)]
        return [0, response]

    def _handle_request(self, hook, args, kwargs):
        if hook not in self._hooks:
            return INVALID_HOOK, None
        try:
            return 0, self._hooks[hook](*args, **kwargs)

        except Exception:
            return RPC_EXCEPTION, traceback.format_exc()

    def _send(self, connection, data):
        data = compact_json(data)
        connection.sendall(data.encode("UTF-8"))

    def _recv(self, connection):
        request = []
        while True:
            data = connection.recv(1024)
            if not data: 
                break
            request.append(data.decode())
            if len(data) < 1024: 
                break
        return json.loads("".join(request))

