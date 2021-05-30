#!/usr/bin/python3

from rpc.utils import compact_json, func_str
import importlib
import json
import socket
import threading
import traceback

ENCRYPTION_PROTOCOLS = [
    "NULL",
    "AES_RSA_CTR"
]

# error codes
SUCCESS = 0
INVALID_HOOK = 1
RPC_EXCEPTION = 2
CRITICAL_ERROR = 3

# used for logging
EXCEPTION_NAMES = [
    None,
    "Requested to call a procedure that isn't hooked.",
    "Exception was raised within the called procedure.",
    "Client interacted with the server without following protocol."
]

class Server:
    def __init__(self, host='', port=8080, verbosity=2):
        self._verbosity = verbosity
        self._host = host
        self._port = port
        self._active = False
        self._hooks = {"handshake": self._handshake}
        self._get_encryption_handlers()

    def _get_encryption_handlers(self):
        self._encryption_handlers = []

        for protocol in ENCRYPTION_PROTOCOLS:
            try:
                handler = importlib.import_module("." + protocol, "rpc").ServerHandler()
                self._encryption_handlers.append(handler)
            except ImportError:
                self._encryption_handlers.append(None)
                if self._verbosity:
                    print(protocol, "is not supported on your system.")

    def add_hook(self, target):
        self._hooks[target.__name__] = target

    def remove_hook(self, target):
        del self._hooks[target.__name__]

    def shutdown(self):
        self._active = False
        self._socket.close()
        if self._verbosity:
            print("Server shut down successfully.")

    def start(self):
        self._active = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._host, self._port))
        self._socket.listen()

        if self._verbosity:
            print("Server started.")

        try:
            while self._active:
                connection, (host, port) = self._socket.accept()

                threading.Thread(
                    target=self._connection_handler,
                    args=(connection, host), daemon=True
                ).start()

        except KeyboardInterrupt:
            self.shutdown()

    def _handshake(self, enc_protocol):
        try:
            handler = self._encryption_handlers[enc_protocol]
            success = True
            public_key = handler.get_public_key()
        except:
            success = False
            public_key = None

        return [success, public_key]

    def _connection_handler(self, connection, host):
        if self._verbosity:
            log_string = "Client request from " + host

        # keep track of whether the RPC was executed
        # the client may want to be informed whether the hook
        # executed after an error occurs
        hook_processed = False

        try:
            auth_layer = self._recv(connection)
            enc_protocol, enc_args, request = \
                self._process_auth_layer(auth_layer)

            response = self._execute_rpc(request)
            hook_processed = True

            if self._verbosity == 2:
                log_string += "\n\t" + func_str(*request)
                log_string += "\n\tEncryption protocol: " + ENCRYPTION_PROTOCOLS[enc_protocol]
                error_code = response[0]
                if error_code:
                    log_string += "\n\tException: " + EXCEPTION_NAMES[error_code]

            # encrypt output
            auth_layer = self._create_auth_layer(enc_protocol, enc_args, response)

        except:
            auth_layer = [0, [], [CRITICAL_ERROR, hook_processed]]
            log_string += "\n\tException: Client didn't follow protocol."

        if self._verbosity:
            print(log_string)

        # send response
        self._send(connection, auth_layer)

    def _process_auth_layer(self, auth_layer):
        enc_protocol, enc_args, data = auth_layer
        handler = self._encryption_handlers[enc_protocol]
        enc_args, decrypted = handler.decrypt(*enc_args, data)
        return enc_protocol, enc_args, decrypted

    def _create_auth_layer(self, enc_protocol, enc_args, response):
        handler = self._encryption_handlers[enc_protocol]
        enc_args, encrypted = handler.encrypt(*enc_args, response)
        return [enc_protocol, enc_args, encrypted]

    def _execute_rpc(self, request):
        hook, args, kwargs = request

        if hook not in self._hooks:
            return INVALID_HOOK, None
        try:
            output = self._hooks[hook](*args, **kwargs)
            return SUCCESS, output

        except Exception:
            return RPC_EXCEPTION, traceback.format_exc()

    def _send(self, connection, data):
        data = compact_json(data)
        connection.sendall(data.encode("UTF-8"))

    def _recv(self, connection):
        received = []
        while True:
            data = connection.recv(1024)
            if not data:
                break
            received.append(data.decode())
            if len(data) < 1024:
                break
        return json.loads("".join(received))

