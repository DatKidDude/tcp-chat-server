import select 
import socket
import sys
from protocol import MessageHeaders

HOST = "localhost"
PORT = 6969

mh = MessageHeaders()

def handle_message(packet: list, has_username: bool):
    """Handles parsing incoming messages from the server"""
    # Checks if the user has successfully logged into the server
    if not has_username:
        if packet[0] == mh.BAD_RQST_HDR:
            print("Error: Unknown issue in previous message header")
        elif packet[0] == mh.BAD_RQST_BODY:
            print("Error: Unknown issue in previous message body.")
        elif packet[0] == mh.IN_USE:
            print(f"Cannot login as <username>. That username is already in use.")
        elif packet[0] == mh.BUSY:
            print("Cannot log in. The server is full!")
        elif packet[0] == mh.BAD_DEST_USR:
            print(f"Cannot log in as <username>. That username contains disallowed characters.")
        else: 
            print(f"Successfully logged in as <username>")
            has_username = True


def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setblocking(False)

    client.connect_ex((HOST, PORT))

    # Sockets from which we expect to read
    inputs = [client, sys.stdin]

    # Socket from which we expect to write
    outputs = []

    # Flag for whether the client is logged into the server
    has_username = False

    print("Welcome to Chat Client. Enter your login: ")
    while client:

        readable, writeable, exceptional = select.select(inputs, outputs, inputs, 0.1)

        for s in readable:
            if s is client:
                data = client.recv(4096)
                if data:
                    packet = data.decode().split()
                    handle_message(packet, has_username)
                    print(packet)
                else:
                    inputs.remove(client)
                    client.close()
                    exit()
            else:
                msg = sys.stdin.readline().strip()
                if not has_username:
                    username = msg.split()[0]
                    packet = f"{mh.HELLO_FROM} {username}\n".encode()
                    client.sendall(packet)
                else:
                    client.sendall(msg.encode())


if __name__ == "__main__":
    start_client()