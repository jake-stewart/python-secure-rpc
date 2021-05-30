import json
import tableprint

try:
    from hashlib import pbkdf2_hmac
    from base64 import b64encode, b64decode
    from os import urandom
    CAN_HASH = 1
except:
    print("WARNING: StudentManager lacks modules necessary for password hashing")
    CAN_HASH = 0


# enum for record fields
PASSWORD_INDEX = 0
RESULTS_INDEX = 1


class StudentDatabase:
    def __init__(self, file_name):
        self._file_name = file_name
        try:
            self.load_from_file()
        except FileNotFoundError:
            print(file_name, "does not exist... Creating new database.")
            self.new_database()

    def __len__(self):
        return len(self._students)

    def __contains__(self, username):
        return username in self._students

    def __str__(self):
        return "StudentDatabase [" + ", ".join(self._students) + "]"

    def get_students(self):
        for student, data in self._students.items():
            yield student, data

    def get_results(self, username):
        return self._students[username][RESULTS_INDEX]

    def ensure_results_validity(self, results):
        for unit_code, result in results:
            assert isinstance(unit_code, str)
            assert len(unit_code) < 20
            assert isinstance(result, float) or isinstance(result, int)
            assert 0 <= result <= 100

    def set_results(self, username, results):
        self.ensure_results_validity(results)
        self._students[username][RESULTS_INDEX] = results

    def new_database(self):
        self._students = {}
        self._hashed = CAN_HASH

    def load_from_file(self):
        with open(self._file_name, "r") as f:
            self._hashed, self._students = json.load(f)

        if self._hashed and not CAN_HASH:
            print(
                "ERROR:", self._file_name,
                "is hashed but the required modules are not installed."
            )
            exit(1)

    def save_to_file(self):
        with open(self._file_name, "w") as f:
            json.dump([self._hashed, self._students], f)

    def add_student(self, username, password):
        if self._hashed:
            salt_bytes = urandom(32)
            password_bytes = password.encode("UTF-8")

            hash_bytes = pbkdf2_hmac(
                "SHA256",
                password_bytes,
                salt_bytes,
                100000
            )

            salt_string = b64encode(salt_bytes).decode()
            hash_string = b64encode(hash_bytes).decode()

            self._students[username] = [[salt_string, hash_string], []]

        else:
            self._students[username] = [password, []]

    def remove_student(self, username):
        del self._students[username]

    def check_credentials(self, username, password):
        if self._hashed:
            try:
                salt_string, actual_hash = self._students[username][PASSWORD_INDEX]
            except KeyError:
                return False

            salt_bytes = b64decode(salt_string)
            password_bytes = password.encode("UTF-8")

            hash_bytes = pbkdf2_hmac(
                "SHA256",
                password_bytes,
                salt_bytes,
                100000
            )

            hash_string = b64encode(hash_bytes).decode()
            return hash_string == actual_hash

        else:
            try:
                return self._students[username][PASSWORD_INDEX] == password
            except KeyError:
                return False

    def print_student_table(self):
        table = []

        for student, data in database.get_students():
            n_units = len(data[RESULTS_INDEX])
            total = sum(result[1] for result in data[RESULTS_INDEX])
            avg = str(round(total / n_units, 2))

            if avg[-3] != ".":
                avg += "0"

            table.append({
                "Username": student,
                "Number of Units": n_units,
                "Average Mark": avg
            })

        tableprint.print_table(table, ["l", "r", "r"], border_style=1)


if __name__ == "__main__":
    from utils import int_input, string_input, clear_screen

    database = StudentDatabase("students.json")
    unsaved_changes = False
    prompt = "> "

    while True:
        try:
            clear_screen()
            print("[1] View students")
            print("[2] Add student")
            print("[3] Delete student")
            print("[4] Reset database")
            print("[5] Save")
            print("[6] Load")
            print("[0] Exit")
            print("")

            choice = int_input(prompt)
            if choice == 1:
                database.print_student_table()

            # add student
            elif choice == 2:
                username = string_input("Username: ", 3, 20)
                if username in database:
                    print("Student already exists.")
                else:
                    password = string_input("Password: ", 3, 20)
                    database.add_student(username, password)
                    print("Student added.")
                    unsaved_changes = True

            # delete student
            elif choice == 3:
                username = input("Username: ")
                if username in database:
                    database.remove_student(username)
                    print("Student removed.")
                    unsaved_changes = True
                else:
                    print("Student does not exist.")

            # reset database
            elif choice == 4:
                print("Are you sure? Type \"I AM SURE\" to proceed.")
                if input(prompt) == "I AM SURE":
                    database.new_database()
                    print("Database reset.")
                    unsaved_changes = True
                else:
                    print("Crisis avoided.")

            # save database
            elif choice == 5:
                database.save_to_file()
                print("Database saved.")
                unsaved_changes = False

            # load database
            elif choice == 6:
                try:
                    database.load_from_file()
                    print("Database loaded.")
                    unsaved_changes = False
                except FileNotFoundError:
                    print("File does not exist.")

            # exit
            elif choice == 0:
                if unsaved_changes:
                    print("You have unsaved changes. Are you sure you want to quit? y/n")
                    if input(prompt).lower() in ("y", "yes"):
                        break
                else:
                    break

            input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            if unsaved_changes:
                print("You have unsaved changes. Are you sure you want to quit? y/n")
                try:
                    if input(prompt).lower() in ("y", "yes"):
                        exit()
                except KeyboardInterrupt:
                    exit()
            else:
                exit()

