class RPCExceptionError(Exception):
    def __init__(self, traceback):
        self.traceback = traceback

    def __str__(self):
        formatted_string = ""
        for line in self.traceback.strip().split("\n"):
            formatted_string += "\n|    " + line
        return formatted_string


class RPCInvalidHookError(Exception):
    def __init__(self, hook=None):
        self.hook = hook

    def __str__(self):
        if self.hook:
            return f"RPC target '{self.hook}()' either doesn't exist, or isn't hooked"
        return "RPC target either doesn't exist, or isn't hooked"


class RPCTimeoutError(Exception):
    def __init__(self, sending):
        self.sending = sending

    def __str__(self):
        if self.sending:
            return "RPC request timed out while sending"
        return "RPC request timed out while receiving reply"


# critical errors SHOULD only call when:
# someone messes with the server.py or client.py source code
# someone performs a replay attack (however, the server will just drop the request and there will be zero damage)
# or very very low chance that a request shares a nonce value with a previous request
# will need to implement retry functionality, so after 5 critical errors (without being processed), it gives up and cries then.
class RPCCriticalError(Exception):
    def __init__(self, hooks_processed):
        self.hooks_processed = hooks_processed

    def __str__(self):
        string = "CRITICAL ERROR. IF YOU DID NOT EDIT THE SOURCE CODE" + \
                 " AND RECIEVED THIS ERROR MESSAGE, REPORT IT IMMEDIATELY. "
        if self.hooks_processed:
            return string + "The RPC request was processed."
        return string + "The RPC request was not processed."
