from rpc.server import Server
from dummy_database import StudentDatabase
import atexit

EVALUATOR_SERVER_TOKEN = "4B4pE0NcQXcaN0-HPqvw371EKyGSwe_6mjX9BC6XoWw"

class DatabaseServer:
    def __init__(self, host, port, database):
        atexit.register(self.on_exit)
        self.database = database
        self.tokens = set()
        self.server = Server(host, port)
        self.server.add_hook(self.database.check_credentials)
        self.server.add_hook(self.database.get_results)
        self.server.add_hook(self.database.set_results)

    def on_exit(self):
        self.database.save_to_file()

    def add_token(self, token):
        self.tokens.add(token)

    def remove_token(self, token):
        self.tokens.remove(token)

    def start(self):
        self.server.start()


if __name__ == "__main__":
    database = StudentDatabase("students.json")

    server = DatabaseServer("", 2000, database)
    server.add_token(EVALUATOR_SERVER_TOKEN)
    server.start()
