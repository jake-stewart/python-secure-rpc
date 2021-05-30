
class ServerHandler:
    def get_public_key(self):
        return None

    def decrypt(self, data):
        return [], data

    def encrypt(self, data):
        return [], data


class ClientHandler:
    def set_public_key(self, _):
        pass

    def encrypt(self, data):
        return [], data

    def decrypt(self, data):
        return data

