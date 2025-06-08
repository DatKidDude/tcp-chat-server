import select 
import socket
import sys
import json
import queue
from protocol import MessageHeaders

HOST = "localhost"
PORT = 6969

mh = MessageHeaders()

def handle_client_input(packet: str):
    """Parses the client messages before sending them to the server"""
    client_message = packet.strip().split()

    # Parses the client commands (!who, !quit)
    # TODO: Add the !quit command
    if client_message[0].startswith("!"):
        command = client_message[0]
        if command == "!who":
            return f"{mh.LIST} {command}\n".encode()
        else:
            print("Command does not exist")
            return None
    
    if client_message[0].startswith("@"):
        username, *msg = client_message
        return f"{mh.SEND} {username} {" ".join(msg)}\n".encode()

    if client_message:
        return f"{mh.BROADCAST} {" ".join(client_message)}\n".encode()


def handle_server_response(packet: str):
    """Parses the server response headers"""

    header, *msg = packet.split()

    if header.startswith(mh.LIST_OK):
        # Turn the users list back into a list object
        users = json.loads(packet.split(" ", 1)[1])
        print(f"There are {len(users)} online users:")
        for user in users:
            print(user)
        return
    
    if header.startswith(mh.SEND_OK):
        print("The message was sent successfully")
        return 
    
    if header.startswith(mh.DELIVERY):
        header, username, *msg = packet.split()
        print(f"From {username}: {" ".join(msg)}")
        return
    
    if header.startswith(mh.BROADCAST_OK):
        print("Message sent")
        return
    elif header.startswith(mh.BROADCAST_DELIVERY):
        header, username, *msg = packet.split()
        print(f"{username}: {" ".join(msg)}")
        return
    else:
        print("Error: Something went wrong")


def handle_login(packet: str, has_username: bool, username: str) -> bool:
    """Handles parsing incoming messages from the server"""

    split_packet = packet.split()

    # Checks if the user has successfully logged into the server
    if not has_username:
        if split_packet[0] == mh.BAD_RQST_HDR:
            print("Error: Unknown issue in previous message header")
        elif split_packet[0] == mh.BAD_RQST_BODY:
            print("Error: Unknown issue in previous message body.")
        elif split_packet[0] == mh.IN_USE:
            print(f"Cannot login as {username}. That username is already in use.")
        elif split_packet[0] == mh.BUSY:
            print("Cannot log in. The server is full!")
        elif split_packet[0] == mh.BAD_DEST_USR:
            print(f"Cannot log in as {username}. That username contains disallowed characters.")
        else: 
            print(f"Successfully logged in as {username}\n")
            has_username = True

    return has_username


def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.setblocking(False)

    client.connect_ex((HOST, PORT))

    # Sockets from which we expect to read
    inputs = [client, sys.stdin]

    # Socket from which we expect to write
    outputs = []

    # Outgoing message queues
    message_queues = {}
    message_queues[client] = queue.Queue()

    # Flag for whether the client is logged into the server
    has_username = False

    print("Welcome to Chat Client. Enter your login: ")
    while client:

        readable, writeable, exceptional = select.select(inputs, outputs, inputs, 0.1)

        for s in readable:
            if s is client:
                data = client.recv(4096)
                if data:
                    packet = data.decode()
                    if not has_username:
                        has_username = handle_login(packet, has_username, username)
                    else:
                        handle_server_response(packet)
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
                    packet = handle_client_input(msg)
                    if packet:
                        client.sendall(packet)
                    else:
                        pass
        
        # for s in writeable:
        #     try:
        #         next_msg = message_queues[s].get_nowait()

if __name__ == "__main__":
    start_client()