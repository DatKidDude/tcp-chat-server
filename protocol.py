from dataclasses import dataclass

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