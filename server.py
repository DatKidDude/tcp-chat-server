import select 
import socket
import queue
from protocol import MessageHeaders

HOST = "localhost"
PORT = 6969
MAX_USERS = 4

users_and_sockets = {}
sockets_and_users = {}

headers = MessageHeaders()

def authenticate_user(message: bytes, client_sock: socket.socket) -> bytes:
    """Authenticates the user on login"""

    FORBIDDEN_CHARS = {"!", "@", "#", "$", "%", "^", "&", "*"}

    split_message = message.decode().strip().split()

    # Message must contain the header and username only
    if len(split_message) > 2:
        return (headers.BAD_RQST_BODY + "\n").encode()
    else:
        header, username = split_message

    # Validate initial handshake header
    if not header.startswith(headers.HELLO_FROM):
        return (headers.BAD_RQST_HDR + "\n").encode()
    
    # Check if the server is full
    if len(users_and_sockets) >= MAX_USERS:
        return (headers.BUSY + "\n").encode()
    
    # Check the length of the username and if it contains banned characters
    if len(username) < 3 or any(char in FORBIDDEN_CHARS for char in username):
        return (headers.BAD_DEST_USR + "\n").encode()
    
    # Check if the username is already taken
    if username in users_and_sockets:
        return (headers.IN_USE + "\n").encode()

    return (headers.HELLO + "\n").encode()
    

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
                    # A readable client socket has data
                    message_queues[s].put(data)
                    # Add output channel for response
                    if s not in outputs:
                        outputs.append(s)
                else:
                    # Interpret empty results as a closed connection
                    print(f"closing {client_address} after reading no data")
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
            # Stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()

            # Remove message queue
            del message_queues[s]


if __name__ == "__main__":
    start_server()