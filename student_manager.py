import json

try:
    from base64 import b64encode, b64decode
    from Crypto.Hash import SHA256
    from Crypto import Random
    HAS_ENCRYPTION = 1

except:
    print("WARNING: StudentManager lacks Pycryptodome necessary for password hashing")
    HAS_ENCRYPTION = 0


class StudentManager:
    def __init__(self, file_name):
        self._file_name = file_name
        self.new()

    def load(self):
        with open(self._file_name) as f:
            self._hashed, self._students = json.load(f)

        if self._hashed and not HAS_ENCRYPTION:
            raise ValueError(
                self._file + " is hashed but Pycryptodome is not installed"
            )

    def new(self):
        self._students = {}
        self._hashed = HAS_ENCRYPTION

    def save(self):
        with open(self._file_name) as f:
            self._students = json.dump(f, [self._hashed, self._students])

    def is_valid(self, username, password):
        if self._hashed:
            try:
                salt_string, hash_string = self._students[username]
            except KeyError:
                return False

            salt_bytes = b64decode(salt_string)

            password_bytes = bytes(password, encoding="UTF-8")

            hasher = SHA256.new()
            hasher.update(salt_bytes + password_bytes)

            return hasher.hexdigest() == hash_string

        else:
            return self._students[username] == password

    def remove(self, username):
        del self._students[username]

    def add(self, username, password):
        if self._hashed:
            password_bytes = bytes(password, encoding="UTF-8")

            salt_bytes = Random.new().read(32)

            hasher = SHA256.new()
            hasher.update(salt_bytes + password_bytes)

            hash_string = hasher.hexdigest()
            salt_string = b64encode(salt_bytes).decode()

            self._students[username] = (salt_string, hash_string)

        else:
            self._students[username] = password

