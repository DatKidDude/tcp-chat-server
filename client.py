import select 
import socket
import sys
from protocol import MessageHeaders

HOST = "localhost"
PORT = 6969

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setblocking(False)

    client.connect_ex((HOST, PORT))

    # Sockets from which we expect to read
    inputs = [client, sys.stdin]

    # Socket from which we expect to write
    outputs = []

    while client:

        readable, writeable, exceptional = select.select(inputs, outputs, inputs, 0.1)

        for s in readable:
            if s is client:
                data = client.recv(4096)
                if data:
                    print(data.decode())
                else:
                    inputs.remove(client)
                    client.close()
                    exit()
            else:
                msg = sys.stdin.readline().strip()
                client.sendall(msg.encode())


if __name__ == "__main__":
    start_client()