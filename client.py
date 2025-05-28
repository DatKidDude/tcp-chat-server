import socket
import sys

messages = [
    "This is the message",
    "It will be sent",
    "in parts.",
]

server_address = ("localhost", 6969)

socks = [
    socket.socket(socket.AF_INET, socket.SOCK_STREAM),
    socket.socket(socket.AF_INET, socket.SOCK_STREAM),
]

print(f"connecting to {server_address[0]}:{server_address[1]}")
for s in socks:
    s.connect(server_address)

for message in messages:

    # Send messages on both sockets
    for s in socks:
        print(f"{s.getsockname()}: sending {message}")
        s.send(message.encode())
    
    # Read responses on both sockets
    for s in socks:
        data = s.recv(1024)
        print(f"{s.getsockname()}: receive {data}")
        if not data:
            print(f"closing socket {s.getsockname()}")
            s.close()
