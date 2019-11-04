from enum import Enum
from collections import namedtuple


class MessageTypes(Enum):
    SYSTEM = 0
    OUTGOING = 1
    INCOMING = 2


class MessageContent(Enum):
    PLAIN = 0
    JSON = 1
    BINARY = 2


SocketMessage = namedtuple('SocketMessage', 'type lines content')
