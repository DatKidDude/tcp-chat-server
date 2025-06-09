import select 
import socket
import sys
import json
import queue
from protocol import MessageHeaders

HOST = "localhost"
PORT = 6969

mh = MessageHeaders()

def handle_client_input(packet: str) -> bytes:
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
            return b""
    
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


def handle_stdin_input(msg: str, has_username: bool) -> bytes:
    """Parses the clients input"""
    
    msg = msg.strip()
    if not msg:
        print("Cannot send an empty message")
        return b""
    
    if not has_username:
        # Strip the rest of the text after the whitespace
        # Username should only be one word
        username = msg.split()[0]
        return f"{mh.HELLO_FROM} {username}\n".encode()
    
    packet = handle_client_input(msg)
    
    return packet or b""
    

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
                    response = handle_server_response(packet, has_username)
                    print(response)
                else:
                    inputs.remove(client)
                    client.close()
                    exit()
            else:
                msg = sys.stdin.readline().strip()
                packet = handle_stdin_input(msg, has_username)
                # If there's no data returned 
                if not packet:
                    continue
                message_queues[client].put(packet)
                if client not in outputs:
                    outputs.append(client)
        
        for s in writeable:
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                # No messages waiting so stop checking
                outputs.remove(s)
            else:
                s.sendall(next_msg)

        for s in exceptional:
            print(f"handling exceptional condition for {s.getpeername()}")
            # Stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()

            # Remove message queue
            del message_queues[s]

if __name__ == "__main__":
    start_client()