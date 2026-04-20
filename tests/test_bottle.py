"""Tests for bottle-protocol."""

import pytest
from bottle_protocol import Bottle, BottleBox, parse_bottle


def test_bottle_creation():
    """Test creating a bottle."""
    bottle = Bottle(
        sender="agent-a",
        recipient="agent-b",
        message="Hello world"
    )
    assert bottle.sender == "agent-a"
    assert bottle.recipient == "agent-b"
    assert bottle.message == "Hello world"
    assert bottle.bottle_id
    assert bottle.timestamp


def test_bottle_to_markdown():
    """Test serializing bottle to markdown."""
    bottle = Bottle(
        sender="agent-a",
        recipient="agent-b",
        message="Hello world",
        metadata={"priority": "high"}
    )
    md = bottle.to_markdown()
    assert "---" in md
    assert "sender: agent-a" in md
    assert "recipient: agent-b" in md
    assert "Hello world" in md
    assert "priority" in md


def test_bottle_hash():
    """Test bottle content hashing."""
    bottle = Bottle(
        sender="agent-a",
        recipient="agent-b",
        message="Test"
    )
    hash_val = bottle.to_hash()
    assert len(hash_val) == 16
    assert isinstance(hash_val, str)


def test_bottle_box_send_receive():
    """Test BottleBox send and receive."""
    box_a = BottleBox("agent-a")
    box_b = BottleBox("agent-b")

    # Send from A to B
    bottle = box_a.send("agent-b", "Test message")
    assert bottle.sender == "agent-a"
    assert bottle.recipient == "agent-b"
    assert len(box_a.get_outbox()) == 1

    # Receive at B
    success = box_b.receive(bottle)
    assert success is True
    assert len(box_b.get_inbox()) == 1

    # Duplicate receive fails
    success = box_b.receive(bottle)
    assert success is False
    assert len(box_b.get_inbox()) == 1


def test_bottle_box_wildcard_recipient():
    """Test wildcard recipient."""
    box = BottleBox("agent-a")
    bottle = Bottle(
        sender="agent-b",
        recipient="*",
        message="Broadcast"
    )
    assert box.receive(bottle) is True


def test_bottle_box_wrong_recipient():
    """Test wrong recipient rejection."""
    box = BottleBox("agent-a")
    bottle = Bottle(
        sender="agent-b",
        recipient="agent-c",
        message="Private"
    )
    assert box.receive(bottle) is False


def test_parse_bottle():
    """Test parsing bottle from markdown."""
    markdown = """---
bottle-id: test-123
sender: agent-a
recipient: agent-b
timestamp: 2024-01-01T00:00:00
---
Hello world"""
    bottle = parse_bottle(markdown)
    assert bottle is not None
    assert bottle.bottle_id == "test-123"
    assert bottle.sender == "agent-a"
    assert bottle.recipient == "agent-b"
    assert bottle.message == "Hello world"


def test_parse_bottle_invalid():
    """Test parsing invalid markdown."""
    assert parse_bottle("not a bottle") is None
    assert parse_bottle("no header\n---\nbody") is None


def test_parse_bottle_with_metadata():
    """Test parsing bottle with metadata."""
    markdown = """---
bottle-id: test-123
sender: agent-a
recipient: agent-b
timestamp: 2024-01-01T00:00:00
metadata:
  priority: high
  tags: ["test", "demo"]
---
Message"""
    bottle = parse_bottle(markdown)
    assert bottle is not None
    assert bottle.metadata.get("priority") == "high"


def test_bottle_roundtrip():
    """Test serialize then parse roundtrip."""
    original = Bottle(
        sender="agent-a",
        recipient="agent-b",
        message="Test",
        metadata={"key": "value"}
    )
    md = original.to_markdown()
    parsed = parse_bottle(md)
    assert parsed is not None
    assert parsed.sender == original.sender
    assert parsed.recipient == original.recipient
    assert parsed.message == original.message
