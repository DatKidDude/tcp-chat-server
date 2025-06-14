import socket
from dataclasses import dataclass

# frozen=True: Makes properties immutable (read-only)
@dataclass(frozen=True) 
class MessageHeaders:
    HELLO: str = "HELLO"
    HELLO_FROM: str = "HELLO-FROM"
    IN_USE: str = "IN-USE"
    BUSY: str = "BUSY"
    LIST: str = "LIST"
    LIST_OK: str = "LIST-OK"
    SEND: str = "SEND"
    SEND_OK: str = "SEND-OK"
    BROADCAST: str = "BROADCAST"
    BROADCAST_OK: str = "BROADCAST-OK"
    BROADCAST_DELIVERY: str = "BROADCAST-DELIVERY"
    BAD_DEST_USR: str = "BAD-DEST-USR"
    DELIVERY: str = "DELIVERY"
    BAD_RQST_HDR: str = "BAD-RQST-HDR"
    BAD_RQST_BODY: str = "BAD-RQST-BODY"


BUFFER_SIZE = 4096
DELIMITER = b"\n"

def recv_data(sock: socket.socket) -> bytes:
    """Keep reading data until the '\n' delimiter is parsed."""
    buffer = b""
    while DELIMITER not in buffer:
        data = sock.recv(BUFFER_SIZE)
        if not data:
            break
        buffer += data
    
    line, sep, buffer = buffer.partition(b"\n")
    
    return line


def send_data(sock: socket.socket, data: bytes) -> None:
    """Uses the number of bytes returned by 'send' to make sure the full message was sent."""
    totalsent = 0
    while totalsent < len(data):
        sent = sock.send(data[totalsent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent
    
    return 
