import select 
import socket
from queue import Queue

HOST = "localhost"
PORT = 6969

users_and_sockets = {}
sockets_and_users = {}

def start_server():
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        readable, writeable, exceptional = select.select(inputs, outputs, inputs)

        # Handle inputs
        for s in readable:

            if s is server:
                # A "readable server socket is ready to accept a connection"
                connection, client_address = server.accept()
                connection.setblocking(False)
                inputs.append(connection)

                # Give the connection a queue for data we want to send
                message_queues[connection] = Queue()
            else:
                data = s.recv(4096)
                if data:
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
        except Queue.empty:
            # No messages waiting so stop checking
            outputs.remove(s)
        else:
            s.send(next_msg)
        
    # Handle "exceptional conditions"
    for s in exceptional:
        # Stop listening for input on the connection
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

        # Remove message queue
        del message_queues[s]


if __name__ == "__main__":
    start_server()