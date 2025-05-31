from dataclasses import dataclass
import json

@dataclass(frozen=True) # Makes dataclass immutable
class Protocol:
    HELLO: str = "HELLO"
    HELLO_FROM: str = "HELLO-FROM"
    LIST: str = "LIST"
    LIST_OK: str = "LIST-OK"
    SEND_OK: str = "SEND-OK"
    SEND: str = "SEND"
    IN_USE: str = "IN-USE"
    BUSY: str = "BUSY"
    BAD_DEST_USER: str = "BAD-DEST-USER"
    DELIVERY: str = "DELIVERY"
    BAD_HEADER: str = "BAD-RQST-HDR"
    BAD_FORMAT: str = "BAD-RQST-BODY"


@dataclass
class Packet:
    header: str = ""
    username: str = ""
    message: str = ""
 
    def to_bytes(self) -> bytes:
        """Converts Packet to json byte string and stores the object's instance variable as a dictionary"""
        return (json.dumps(self.__dict__) + "\n").encode()

    @staticmethod
    def from_bytes(data: bytes) -> "Packet":
        """Decodes json byte string and returns a Packet object"""
        obj = json.loads(data.decode())
        return Packet(**obj)
