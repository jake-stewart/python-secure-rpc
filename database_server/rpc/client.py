#!/usr/bin/python3

from rpc.exceptions import *
from rpc.utils import compact_json
import importlib
import json
import socket

ENCRYPTION_PROTOCOLS = [
    "NULL",
    "AES_RSA_CTR"
]

# error codes
SUCCESS = 0
INVALID_HOOK = 1
RPC_EXCEPTION = 2
CRITICAL_ERROR = 3

class Client:
    def __init__(self, host, port, enc_protocol="NULL"):
        self._host = host
        self._port = port
        self._timeout = 10
        self._hook = None
        self._enc_protocol = 0
        self._desired_protocol = ENCRYPTION_PROTOCOLS.index(enc_protocol)
        self._enc_handler = self._get_enc_handler(0)

    def _get_enc_handler(self, enc_protocol):
        module_name = ENCRYPTION_PROTOCOLS[enc_protocol]
        module = importlib.import_module("." + module_name, "rpc")
        return module.ClientHandler()

    def __getattr__(self, attr):
        self._hook = attr
        return self._rpc_wrapper

    def _rpc_wrapper(self, *args, **kwargs):
        return self.rpc_request(self._hook, args, kwargs)

    def set_timeout(self, timeout):
        self._timeout = timeout

    def connect(self):
        response = self.rpc_request("handshake", args=[self._desired_protocol])

        if self._desired_protocol:
            self._null_enc_handler = self._enc_handler
            self._enc_handler = self._get_enc_handler(self._desired_protocol)

            _, public_key = response
            self._enc_protocol = self._desired_protocol
            self._enc_handler.set_public_key(public_key)

    def rpc_request(self, hook, args=[], kwargs={}):
        # populate request data
        request = [hook, args, kwargs]

        # add authentication/encryption layer
        auth_layer = self._create_auth_layer(request)

        # connect to server
        soc = self._create_socket()

        # send request
        try:
            self._send(soc, auth_layer)
        except socket.timeout:
            raise RPCTimeoutError(sending=True)

        # recieve reply
        try:
            auth_layer = self._recv(soc)
        except socket.timeout:
            raise RPCTimeoutError(sending=False)

        # close connection with server
        soc.close()

        # process authentication layer (decrypt data)
        error_code, response = self._process_auth_layer(auth_layer)

        # raise error if one exists
        if error_code:
            if error_code == INVALID_HOOK:
                raise RPCInvalidHookError(response)
            elif error_code == RPC_EXCEPTION:
                raise RPCExceptionError(response)
            elif error_code == CRITICAL_ERROR:
                raise RPCCriticalError(response)

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
        received = []
        while True:
            data = soc.recv(1024)
            if not data:
                break
            received.append(data.decode())
            if len(data) < 1024:
                break
        return json.loads("".join(received))

    def _create_auth_layer(self, request):
        enc_args, encrypted = self._enc_handler.encrypt(request)
        auth_layer = [
            self._enc_protocol,
            enc_args,
            encrypted
        ]
        return auth_layer

    def _process_auth_layer(self, auth_layer):
        enc_protocol, enc_args, encrypted = auth_layer
        if enc_protocol == self._enc_protocol:
            return self._enc_handler.decrypt(*enc_args, encrypted)
        elif not enc_protocol:
            return self._null_enc_handler.decrypt(*enc_args, encrypted)
        else:
            raise CriticalError("Server did not follow protocol.")


def connect(host, port, encryption="NULL"):
    client = Client(host, port, enc_protocol=encryption)
    client.connect()
    return client

