"""Tests for bottle-protocol — git-native agent messaging."""
from bottle_protocol import Bottle, BottleBox, parse_bottle

def test_bottle_create():
    b = Bottle(sender="oracle1", recipient="fm", message="Build the thing")
    assert b.sender == "oracle1"
    assert b.bottle_id
    print("PASS: bottle create")

def test_bottle_markdown_roundtrip():
    b = Bottle(sender="a", recipient="b", message="hello fleet")
    md = b.to_markdown()
    assert "---" in md
    assert "sender: a" in md
    parsed = parse_bottle(md)
    assert parsed.sender == "a"
    assert parsed.message == "hello fleet"
    print("PASS: markdown roundtrip")

def test_bottlebox_send_receive():
    box = BottleBox(agent_id="oracle1")
    b = box.send("fm", "Deploy the crates")
    assert len(box.get_outbox()) == 1
    fm_box = BottleBox(agent_id="fm")
    assert fm_box.receive(b) is True
    assert len(fm_box.get_inbox()) == 1
    assert fm_box.receive(b) is False
    print("PASS: send/receive")

def test_bottlebox_wrong_recipient():
    box = BottleBox(agent_id="oracle1")
    b = box.send("fm", "Secret message")
    jc1_box = BottleBox(agent_id="jc1")
    assert jc1_box.receive(b) is False
    print("PASS: wrong recipient rejected")

def test_broadcast():
    box = BottleBox(agent_id="oracle1")
    b = box.send("*", "Fleet announcement")
    fm_box = BottleBox(agent_id="fm")
    jc1_box = BottleBox(agent_id="jc1")
    assert fm_box.receive(b) is True
    assert jc1_box.receive(b) is True
    print("PASS: broadcast")

def test_hash_dedup():
    b1 = Bottle(sender="a", recipient="b", message="same", timestamp="2026-01-01")
    b2 = Bottle(sender="a", recipient="b", message="same", timestamp="2026-01-01")
    assert b1.to_hash() == b2.to_hash()
    print("PASS: hash dedup")

if __name__ == "__main__":
    test_bottle_create()
    test_bottle_markdown_roundtrip()
    test_bottlebox_send_receive()
    test_bottlebox_wrong_recipient()
    test_broadcast()
    test_hash_dedup()
    print("\nAll 6 pass. Bottles float between ships.")
