from rpc_client import connect

HOST = 'localhost'
PORT = 8080

credentials = ("jake", "12345")

conn = connect(HOST, PORT)

# fib() requires authentication, so we pass our username/password
print(conn.fib(credentials, 100))

# add() does not require authentication
print(conn.add(4, 5))
