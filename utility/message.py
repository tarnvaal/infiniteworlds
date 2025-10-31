# message.py
from datetime import datetime
from typing import Optional


class Message:
    """
    This is used to represent a message in the history.
    - Tokens is the approximate token count of the message.
    - The caller is responsible for calculating the tokens.

    Mutation Policy:
    - After initialization, the 'role', 'content', 'tokens', 'timestamp', 'id' should be treated as immutable.
    - Only active should be mutated.
    """

    def __init__(
        self,
        role: str,
        content: str,
        tokens: int,
        msg_id: Optional[int] = None,
        active: bool = True,
        timestamp: Optional[datetime] = None,
    ):
        self.role = role
        self.content = content
        self.tokens = tokens
        self.id = msg_id
        self.timestamp = timestamp if timestamp is not None else datetime.now()
        self.active = active

    def deactivate(self) -> None:
        self.active = False

    def activate(self) -> None:
        self.active = True

    def is_active(self) -> bool:
        return self.active

    def __str__(self) -> str:
        return f"{self.role}: {self.content}"

    def __repr__(self) -> str:
        return (
            f"Message(id={self.id}, role={self.role!r}, "
            f"active={self.active}, tokens={self.tokens}, "
            f"timestamp={self.timestamp.isoformat()}, "
            f"content={self.content!r})"
        )
