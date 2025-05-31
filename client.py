from protocol import Packet
import socket

p = Packet(header="HELL-FROM", username="bill", message="")
packet = p.to_bytes()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
    client.connect(("127.0.0.1", 6969))

    client.sendall(packet)
    data = client.recv(4096)
    print(data.decode())
    client.close()



