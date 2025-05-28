from protocol import Protocol
import socket
import select
import sys
import queue
import typing

HOST = "127.0.0.1"
PORT = 6969
MAX_CONNECTIONS = 4
# Instantiate the protocol class
p = Protocol()

def handshake(message: bytes, users):
    """Retrieves the user's name to login in to the chat server"""
    message_str = message.decode().strip("")
    # TODO: Add newline after each message
    # check if message startswith HELLO-FROM
    if not message_str.startswith(p.HELLO_FROM):
        print(message_str)
        return p.BAD_HEADER.encode()
    
    # check if room is full
    if len(users) == MAX_CONNECTIONS:
        return p.BUSY.encode()
    
    # check if username is in use
    username = message_str.split(" ")[-1]
    if username.lower() in users:
        return p.BAD_DEST_USER.encode()
    
    return f"{p.HELLO} {username}".encode()

def main():
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow socket to reuse address 
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setblocking(False)

    # Bind socket to host machine
    server.bind((HOST, PORT))
    print(f"starting up on {HOST}:{PORT}", file=sys.stderr)
    # Listen for incoming connections
    server.listen()

    # Sockets from which we expect to read
    inputs: list[socket.socket] = [server]

    # Sockets to which we expect to write
    outputs: list[socket.socket] = []

    # Outgoing message queues
    message_queues: dict[socket.socket, queue.Queue] = {}

    # logged in users
    users: dict[str, socket.socket] = {}

    while inputs:
        # Wait for at least one of the sockets to be ready for processing
        print("waiting for the next event", file=sys.stderr)
        readable, writeable, exceptional = select.select(inputs, outputs, inputs)

        # Handle inputs 
        for s in readable:

            if s is server:
                # A "readable" server socket is ready to accept a connection
                connection, client_address = s.accept()
                print(f"new connection from {client_address}", file=sys.stderr)
                connection.setblocking(False)
                inputs.append(connection)

                # Give the connection a queue for data we want to send
                message_queues[connection] = queue.Queue()
            else:
                data = s.recv(1024)
                if data:
                    # A readable client socket has data
                    print(f"received {data} from {s.getpeername()}")
                    # TODO: Implement the handshake
                    response = handshake(data, users)

                    message_queues[s].put(response)
                    # Add a channel for output response
                    if s not in outputs:
                        outputs.append(s)
                else:
                    # Interpret empty result as closed connection
                    print(f"closing {client_address} after reading no data", file=sys.stderr)
                    # Stop listening for the input on the connection
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()

                    # Remove message queue
                    del message_queues[s]
        
        # Handle outputs
        for s in writeable:
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                # No message waiting so stop checking for writability
                print(f"output queue for {s.getpeername()} is empty", file=sys.stderr)
                outputs.remove(s)
            else:
                print(f"sending {next_msg} to {s.getpeername()}", file=sys.stderr)
                s.send(next_msg)
        
        # Handle exceptional conditions
        for s in exceptional:
            print(f"handling exceptional conditions for {s.getpeername()}", file=sys.stderr)
            # Stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()

            # Remove message queue
            del message_queues[s]

if __name__ == "__main__":
    main()