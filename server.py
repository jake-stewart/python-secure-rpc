from rpc_server import Server
from student_manager import StudentManager

FILE_NAME = "students.json"
HOST = ""
PORT = 8080

def add(a, b):
    return a + b

def fib(credentials, n):
    if not student_manager.is_valid(*credentials):
        return None

    a, b = 0, 1
    nums = []
    while a < n:
        nums.append(a)
        a, b = b, a+b
    return " ".join(map(str, nums))


if __name__ == "__main__":
    student_manager = StudentManager(FILE_NAME)
    try:
        student_manager.load()
    except FileNotFoundError:
        pass

    student_manager.add("jake", "12345")

    # create rpc server
    server = Server(HOST, PORT)

    # add rpc hooks that clients can trigger
    server.add_hook(fib)
    server.add_hook(add)

    server.start()
