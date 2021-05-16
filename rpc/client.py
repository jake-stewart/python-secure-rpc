#!/usr/bin/python3

import socket
import json
from rpc.utils import compact_json
from rpc.exceptions import *

try:
    from rpc.aes_rsa_encryption import ClientEncryptionHandler
    HAS_ENCRYPTION = True
except:
    # in a production setting, this application would come
    # with the encryption library installed. The ability
    # to use this module without encryption is just for
    # the marker's convienence of not having to install
    # Pycryptodome.

    print("WARNING: NO ENCRYPTION LIBRARY INSTALLED")
    print("Install Pycryptodome before sending confidential information.")
    HAS_ENCRYPTION = False


# error codes
INVALID_HOOK = 1
RPC_EXCEPTION = 2
CRITICAL_ERROR = 3

class Client:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._timeout = 10
        self._hook = None
        self._encryption_handler = None

    def __getattr__(self, attr):
        self._hook = attr
        return self._rpc_wrapper

    def _rpc_wrapper(self, *args, **kwargs):
        return self.rpc_request(self._hook, args, kwargs)

    def set_timeout(self, timeout):
        self._timeout = timeout

    def connect(self):
        response = self.rpc_request("connect", args=[HAS_ENCRYPTION])
        server_encrypted, secret = response

        # only create encryption handler if both client and server
        # has support for it
        if HAS_ENCRYPTION:
            if server_encrypted:
                self._encryption_handler = ClientEncryptionHandler(secret)
            else:
                print("WARNING: SERVER DOES NOT SUPPORT ENCRYPTION")

    def rpc_request(self, hook, args=[], kwargs={}):
        # populate request data
        request = [hook, args, kwargs]

        # add encryption header
        encryption_layer = self._create_encryption_layer(request)

        # connect to server
        soc = self._create_socket()

        # send request
        try:
            self._send(soc, encryption_layer)
        except socket.timeout:
            raise RPCTimeoutError(sending=True)

        # recieve reply
        try:
            error_code, response = self.recv_reply(soc)
        except socket.timeout:
            raise RPCTimeoutError(sending=False)

        # raise error if exists
        if error_code:
            if error_code == INVALID_HOOK:
                raise RPCInvalidHookError(response)
            elif error_code == RPC_EXCEPTION:
                raise RPCExceptionError(response)
            elif error_code == CRITICAL_ERROR:
                raise RPCCriticalError(response)

        # close connection with server
        soc.close()

        # return response
        return response

    def _create_socket(self):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        soc.settimeout(self._timeout)
        soc.connect((self._host, self._port))
        return soc

    def _send(self, soc, request):
        message = compact_json(request)
        soc.sendall(message.encode("UTF-8"))

    def _recv(self, soc):
        response = []
        while True:
            data = soc.recv(1024)
            if not data:
                break
            response.append(data.decode())
            if len(data) < 1024:
                break
        return json.loads("".join(response))

    def _create_encryption_layer(self, request):
        if self._encryption_handler:
            json_request = compact_json(request)
            encryption_layer = [
                True, *self._encryption_handler.encrypt(json_request)
            ]
        else:
            encryption_layer = [False, request]

        return encryption_layer

    def recv_reply(self, soc):
        encryption_layer = self._recv(soc)
        encrypted, *args, response = encryption_layer
        if encrypted:
            response = self._encryption_handler.decrypt(*args, response)

        return response


def connect(host, port):
    client = Client(host, port)
    client.connect()
    return client

