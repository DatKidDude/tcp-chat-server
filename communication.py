"""Holds the send and receive functions for parsing socket messages"""
import socket
BUFFER_SIZE = 4096

def recv_message(sock: socket.socket) -> bytes:
    """Delimiter based receive method to find the end of the message"""
    data = sock.recv(BUFFER_SIZE)
    buffer = b""
    while b"\n" not in buffer:
        if not data:
            break
        buffer += data
    line, sep, buffer = buffer.partition(b"\n")
    return line


def send_message():
    pass