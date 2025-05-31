from protocol import Protocol, Packet
from communication import recv_message, send_message
import socket
import select
import sys
import queue
import typing
import string

HOST = "127.0.0.1"
PORT = 6969
MAX_CONNECTIONS = 4
# Instantiate the protocol class
p: Protocol = Protocol()


def parse_user_messages(sock: socket.socket,
                        message: bytes,
                        session_users: dict[str, socket.socket]) -> bytes:
    """Parse the message header and any commands"""
    message_str = message.decode().strip()

    # Client uses the !who command
    if message_str.startswith(p.LIST):
        all_active_users  = ",".join(user for user in session_users)
        return (f"{p.LIST_OK} {all_active_users}\n").encode()
    
    # SEND [name] [message]


def remove_user_from_session(sock: socket.socket, 
                             session_users: dict[str, socket.socket], 
                             session_sockets: dict[socket.socket, str]):
    """Removes the user and socket from the session dictionaries"""

    # Retrieve the username
    username = session_sockets.pop(sock, None)
    if username:
        session_users.pop(username, None)


def authenticate_user(sock: socket.socket,
                      packet: bytes,  
                      session_users: dict[str, socket.socket], 
                      session_sockets: dict[socket.socket, str]) -> bytes:
    """Retrieves the user's name to login in to the chat server and adds it to the session"""
    recv_packet = Packet.from_bytes(packet)
    username = recv_packet.username if recv_packet.username else ""
    message = recv_packet.message if recv_packet.message else ""

    # Only allow letter and digit characters (Whitelist approach)
    WHITELIST_CHARS = string.ascii_letters + string.digits
   
    # Check if message startswith HELLO-FROM
    if not recv_packet.header.startswith(p.HELLO_FROM):
        return Packet(header=p.BAD_HEADER, username="", message="Error: Unknown issue in previous message header.").to_bytes()          
       
    # Check if room is full
    if len(session_users) >= MAX_CONNECTIONS:
        return Packet(header=p.BUSY, username=username, message=message).to_bytes()

    # Validate username length and against whitelist
    if len(username) >= 3:
        if any(char not in WHITELIST_CHARS for char in username):
            return (p.BAD_FORMAT + "\n").encode()

    # # Check if username is in use
    # if username_lower in session_users:
    #     return (p.BAD_DEST_USER + "\n").encode()
    
    # # Add users to session
    # session_users.update({username_lower: sock})
    # session_sockets.update({sock: username_lower})

    # return f"{p.HELLO} {username_lower}\n".encode()


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

    # logged in session_users (using two mappings)
    session_users: dict[str, socket.socket] = {}
    session_sockets: dict[socket.socket, str] = {}

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
                data = recv_message(s)
                if data:
                    # A readable client socket has data
                    print(f"received {data} from {s.getpeername()}")
                    
                    # Check if the user is already authenticated
                    if s not in session_sockets:
                        data = authenticate_user(s, data, session_users, session_sockets)
                    else:
                        data = parse_user_messages(s, data, session_users) 
            
                    message_queues[s].put(data)
                    # Add a channel for output response
                    if s not in outputs:
                        outputs.append(s)
                else:
                    # Interpret empty result as closed connection
                    print(f"closing {client_address} after reading no data", file=sys.stderr)
                    # Remove the user from the session
                    remove_user_from_session(s, session_users, session_sockets)
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
            # Remove the user from the session
            remove_user_from_session(s, session_users, session_sockets)
            # Stop listening for input on the connection
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()

            # Remove message queue
            del message_queues[s]

if __name__ == "__main__":
    main()