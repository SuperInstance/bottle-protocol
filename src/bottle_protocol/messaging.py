"""
Core messaging primitives for bottle protocol.

Bottles are immutable message containers that can be stored in git
and exchanged between agents.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Message:
    """A message payload sent between agents."""

    sender: str
    recipient: str
    payload: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    message_id: Optional[str] = None

    def __post_init__(self):
        if self.message_id is None:
            content = f"{self.sender}:{self.recipient}:{self.timestamp}:{json.dumps(self.payload, sort_keys=True)}"
            self.message_id = hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            sender=data["sender"],
            recipient=data["recipient"],
            payload=data["payload"],
            timestamp=data["timestamp"],
            message_id=data["message_id"]
        )


@dataclass
class Bottle:
    """A sealed bottle containing messages for git storage."""

    messages: list[Message]
    bottle_id: str
    schema_version: str = "0.1.0"
    created_at: float = field(default_factory=time.time)

    def add_message(self, message: Message) -> None:
        """Add a message to this bottle."""
        if message.message_id in [m.message_id for m in self.messages]:
            raise ValueError(f"Message {message.message_id} already in bottle")
        self.messages.append(message)

    def to_bytes(self) -> bytes:
        """Serialize bottle to bytes for git storage."""
        data = {
            "bottle_id": self.bottle_id,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "messages": [m.to_dict() for m in self.messages]
        }
        return json.dumps(data, sort_keys=True).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> "Bottle":
        """Deserialize bottle from bytes."""
        parsed = json.loads(data.decode())
        messages = [Message.from_dict(m) for m in parsed["messages"]]
        return cls(
            messages=messages,
            bottle_id=parsed["bottle_id"],
            schema_version=parsed["schema_version"],
            created_at=parsed["created_at"]
        )

    def messages_for(self, recipient: str) -> list[Message]:
        """Get all messages for a specific recipient."""
        return [m for m in self.messages if m.recipient == recipient]


class BottleOpener:
    """Utility for opening and managing bottles."""

    @staticmethod
    def create_bottle(bottle_id: str) -> Bottle:
        """Create a new empty bottle."""
        return Bottle(messages=[], bottle_id=bottle_id)

    @staticmethod
    def merge_bottles(bottles: list[Bottle]) -> Bottle:
        """Merge multiple bottles into one."""
        if not bottles:
            raise ValueError("Cannot merge empty bottle list")

        all_messages = []
        seen_ids = set()

        for bottle in bottles:
            for msg in bottle.messages:
                if msg.message_id not in seen_ids:
                    all_messages.append(msg)
                    seen_ids.add(msg.message_id)

        # Create merged bottle ID from all source IDs
        merged_id = hashlib.sha256(
            ":".join(sorted(b.bottle_id for b in bottles)).encode()
        ).hexdigest()[:16]

        return Bottle(messages=all_messages, bottle_id=merged_id)

    @staticmethod
    def validate_bottle(bottle: Bottle) -> bool:
        """Validate bottle structure and contents."""
        if not bottle.bottle_id:
            return False

        if not bottle.schema_version:
            return False

        for msg in bottle.messages:
            if not msg.sender or not msg.recipient:
                return False
            if msg.message_id is None:
                return False

        return True
