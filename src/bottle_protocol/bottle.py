"""Bottle messaging implementation."""

import hashlib
import re
import json
import uuid
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Bottle:
    """A message bottle sent between agents via git."""

    sender: str
    recipient: str
    message: str
    bottle_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Serialize bottle to git-commit-friendly markdown format."""
        lines = [
            "---",
            f"bottle-id: {self.bottle_id}",
            f"sender: {self.sender}",
            f"recipient: {self.recipient}",
            f"timestamp: {self.timestamp}",
        ]
        if self.metadata:
            lines.append("metadata:")
            for key, value in self.metadata.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"  {key}: {json.dumps(value)}")
                else:
                    lines.append(f"  {key}: {value}")
        lines.append("---")
        lines.append(self.message)
        return "\n".join(lines)

    def to_hash(self) -> str:
        """Compute content hash for deduplication."""
        content = f"{self.sender}:{self.recipient}:{self.message}:{self.timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class BottleBox:
    """Inbox/outbox for bottle messages."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self._inbox: List[Bottle] = []
        self._outbox: List[Bottle] = []
        self._sent_ids: set = set()
        self._processed_ids: set = set()

    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> Bottle:
        """Create and queue a bottle for sending."""
        bottle = Bottle(
            sender=self.agent_id,
            recipient=recipient,
            message=message,
            metadata=metadata or {}
        )
        self._outbox.append(bottle)
        self._sent_ids.add(bottle.bottle_id)
        return bottle

    def receive(self, bottle: Bottle) -> bool:
        """Receive a bottle into inbox if not already processed."""
        if bottle.bottle_id in self._processed_ids:
            return False
        if bottle.recipient != self.agent_id and bottle.recipient != "*":
            return False
        self._inbox.append(bottle)
        self._processed_ids.add(bottle.bottle_id)
        return True

    def get_inbox(self) -> List[Bottle]:
        """Get all received bottles."""
        return list(self._inbox)

    def get_outbox(self) -> List[Bottle]:
        """Get all unsent bottles."""
        return list(self._outbox)

    def clear_outbox(self) -> None:
        """Clear outbox after sending."""
        self._outbox.clear()

    def mark_sent(self, bottle_id: str) -> bool:
        """Mark a bottle as sent (e.g., after git commit)."""
        if bottle_id in self._sent_ids:
            self._sent_ids.discard(bottle_id)
            return True
        return False


def parse_bottle(markdown: str) -> Optional[Bottle]:
    """Parse a bottle from markdown format.

    Format:
    ---
    bottle-id: <id>
    sender: <agent>
    recipient: <agent>
    timestamp: <iso>
    metadata:
      key: value
    ---
    <message body>
    """
    pattern = r'^---\n(.*?)\n---\n(.*)$'
    match = re.match(pattern, markdown, re.DOTALL)
    if not match:
        return None

    header, message = match.groups()
    data = {}

    for line in header.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip()

    # Parse metadata if present
    metadata = {}
    if 'metadata' in data:
        # Simple key-value parsing from metadata section
        current_key = None
        in_metadata = False
        for line in header.strip().split('\n'):
            if line.strip().startswith('metadata:'):
                in_metadata = True
                continue
            if in_metadata:
                if line.startswith('  ') and ':' in line:
                    key, value = line.split(':', 1)
                    current_key = key.strip()
                    try:
                        metadata[current_key] = json.loads(value.strip())
                    except:
                        metadata[current_key] = value.strip()
                elif not line.startswith('  '):
                    break

    try:
        return Bottle(
            bottle_id=data.get('bottle-id', ''),
            sender=data.get('sender', ''),
            recipient=data.get('recipient', ''),
            timestamp=data.get('timestamp', ''),
            message=message.strip(),
            metadata=metadata
        )
    except (KeyError, ValueError):
        return None
