import select 
import socket
import queue
import json
from protocol import MessageHeaders

HOST = "localhost"
PORT = 6969
MAX_USERS = 4

# Keeps track of currently active users
users_and_sockets = {}
sockets_and_users = {}

mh = MessageHeaders()

def handle_messages(message: bytes, 
                    client_sock: socket.socket, 
                    message_queues: dict[str, queue.Queue], 
                    outputs: list
                    ) -> bytes:
    """Parse the user's incoming messages"""
    header, *msg = message.decode().strip().split()
    
    # Return a list of users in the chatroom
    if header.startswith(mh.LIST):
        active_users = [user for user in users_and_sockets]
        return f"{mh.LIST_OK} {json.dumps(active_users)}\n".encode()

    # Sends direct messages to user
    if header.startswith(mh.SEND):
        username, *private_message = msg
        if username in users_and_sockets:
            private_message = " ".join(private_message)
            # Person sending the message
            sender_name = sockets_and_users[client_sock] 

            # Person receiving the message
            receiver_name = users_and_sockets[username]

            # Add receiver to outputs list
            outputs.append(receiver_name)

            packet = f"{mh.DELIVERY} {sender_name} {private_message}\n".encode()

            # Add the message to the receiver's queue 
            message_queues[receiver_name].put(packet)

            # Send an ok status message back to the user
            return f"{mh.SEND_OK}\n".encode()
        else:
            # User doesn't exist
            return (mh.BAD_DEST_USR + "\n").encode()

    # Broadcast message to all users 
    if header.startswith(mh.BROADCAST):
        broadcast_message = " ".join(msg)
        sender_name = sockets_and_users[client_sock]
        for user in users_and_sockets:
            receiver_name = users_and_sockets[user]
            outputs.append(receiver_name)
            packet = f"{mh.BROADCAST_DELIVERY} {sender_name} {broadcast_message}\n".encode()
            message_queues[receiver_name].put(packet)
            return (mh.BROADCAST_OK + "\n").encode()

    return (mh.BAD_RQST_BODY + "\n").encode()


def remove_user(client_sock: socket.socket) -> None:
    """Remove the user from the two dictionaries"""
    if client_sock in sockets_and_users:
        username = sockets_and_users.pop(client_sock)
        del users_and_sockets[username]


def authenticate_user(message: bytes, client_sock: socket.socket) -> bytes:
    """Authenticates the user on login"""

    FORBIDDEN_CHARS = {"!", "@", "#", "$", "%", "^", "&", "*"}

    split_message = message.decode().strip().split()

    # Message must contain the header and username only
    if len(split_message) > 2:
        return (mh.BAD_RQST_BODY + "\n").encode()
    else:
        header, username = split_message

    # Validate initial handshake header
    if not header.startswith(mh.HELLO_FROM):
        return (mh.BAD_RQST_HDR + "\n").encode()
    
    # Check if the server is full
    if len(users_and_sockets) >= MAX_USERS:
        return (mh.BUSY + "\n").encode()
    
    # Check the length of the username and if it contains banned characters
    # TODO: Need to separate these according to specification
    if len(username) < 3 or any(char in FORBIDDEN_CHARS for char in username):
        return (mh.BAD_DEST_USR + "\n").encode()
    
    # Check if the username is already taken
    if username in users_and_sockets:
        return (mh.IN_USE + "\n").encode()

    users_and_sockets.update({username: client_sock})
    sockets_and_users.update({client_sock: username})

    return f"{mh.HELLO} {username}\n".encode()
    

def start_server():
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(False)

    # Bind the socke to the port
    print(f"Starting server on {HOST}:{PORT}")
    server.bind((HOST, PORT))

    # Listen for incoming connections 
    server.listen()

    # Sockets from which we expect to read
    inputs = [server]

    # Socket from which we expect to write
    outputs = []

    # Outgoing message queues
    message_queues = {}

    while inputs:

        # Wait for at least one of the sockets to become ready for processing (Select will block with no timeout set)
        print(f"\nwaiting for the next event")
        readable, writeable, exceptional = select.select(inputs, outputs, inputs)

        # Handle inputs
        for s in readable:

            if s is server:
                # A "readable server socket is ready to accept a connection"
                connection, client_address = server.accept()
                print(f"new connection from {client_address}")
                connection.setblocking(False)
                inputs.append(connection)

                # Give the connection a queue for data we want to send
                message_queues[connection] = queue.Queue()
            else:
                data = s.recv(4096)
                if data:
                    print(f"received {data} from {s.getpeername()}")
                    if s not in sockets_and_users:
                        data = authenticate_user(data, s)
                    else:
                        data = handle_messages(data, s, message_queues, outputs)
                    # A readable client socket has data
                    message_queues[s].put(data)
                    # Add output channel for response
                    if s not in outputs:
                        outputs.append(s)
                else:
                    # Interpret empty results as a closed connection
                    print(f"closing {client_address} after reading no data")
                    remove_user(s)
                    # Stop listening for input on the connection
                    inputs.remove(s)
                    s.close()

                    # Remove message queue
                    del message_queues[s]

        # Handle outputs
        for s in writeable:
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                # No messages waiting so stop checking
                print(f"output queue for {s.getpeername()} is empty")
                outputs.remove(s)
            else:
                s.send(next_msg)
            
        # Handle "exceptional conditions"
        for s in exceptional:
            print(f"handling exceptional condition for {s.getpeername()}")
            remove_user(s)
            # Stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()

            # Remove message queue
            del message_queues[s]


if __name__ == "__main__":
    start_server()