from rpc.server import Server
from rpc.client import connect
import secrets


TOKEN = "4B4pE0NcQXcaN0-HPqvw371EKyGSwe_6mjX9BC6XoWw"


class EvaluatorServer:
    def __init__(self, database_con, host, port, token_strength=32):
        self.database = database_con
        self.token_strength = token_strength
        self.server = Server(host, port)
        self.server.add_hook(self.log_in)
        self.server.add_hook(self.evaluate_eligibility)
        self.server.add_hook(self.get_results)
        self.server.add_hook(self.set_results)

        self.tokens = {}
        self.reversed_tokens = {}

    def start(self):
        self.server.start()

    def log_in(self, username, password):
        if not self.database.check_credentials(username, password):
            return False

        # delete old token if it exists
        if username in self.reversed_tokens:
            token = self.reversed_tokens[username]
            del self.reversed_tokens[username]
            del self.tokens[token]

        # create new token
        token = secrets.token_urlsafe(self.token_strength)

        # link token to username
        self.tokens[token] = username
        self.reversed_tokens[username] = token

        return token

    def get_results(self, token):
        username = self.tokens[token]
        return self.database.get_results(username)

    def set_results(self, token, results):
        username = self.tokens[token]
        self.database.set_results(username, results)

    def evaluate_eligibility(self, token, units):
        if token not in self.tokens:
            return None
        username = self.tokens[token]

        n_fails = 0
        total = 0
        n_units = len(units)


        for unit_code, mark in units:
            if mark < 50:
                n_fails += 1
            total += mark

        average = total / n_units
        top_12 = sorted(list(zip(*units))[1], reverse=True)[:12]
        top_12_average = sum(top_12) / 12

        if n_fails >= 6 or len(units) < 12:
            evaluation = "DOES NOT QUALIFY FOR HONOURS STUDY!"

        elif average >= 70:
            evaluation = "QUALIFIED FOR HONOURS STUDY!"

        else:
            if top_12_average >= 80:
                evaluation = "MAY HAVE A GOOD CHANCE! Need further asssessment!"

            elif top_12_average >= 70:
                evaluation = "MAY HAVE A CHANCE!\nMust be carefully " + \
                    "reassessed and get the coordinator's special permission!"

            else:
                evaluation = "DOES NOT QUALIFY FOR HONOURS STUDY!\n" + \
                    "Try masters by course work."

        return username, average, top_12_average, evaluation


if __name__ == "__main__":
    database_con = connect("localhost", 2000)
    server = EvaluatorServer(database_con, "", 8080)
    server.start()
