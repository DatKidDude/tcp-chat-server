from dataclasses import dataclass

# frozen=True: Makes properties immutable (read-only)
@dataclass(frozen=True) 
class MessageHeaders:
    HELLO: str = "HELLO"
    HELLO_FROM: str = "HELLO-FROM"
    IN_USE: str = "IN-USE"
    BUSY: str = "BUSY"
    LIST_OK: str = "LIST-OK"
    SEND_OK: str = "SEND-OK"
    BAD_DEST_USR: str = "BAD-DEST-USR"
    DELIVERY: str = "DELIVERY"
    BAD_RQST_HDR: str = "BAD-RQST-HDR"
    BAD_RQST_BODY: str = "BAD-RQST-BODY"