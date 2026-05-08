# Bottle Protocol

**Git-native agent-to-agent messaging. Float a bottle, someone reads it, they reply. That's the protocol.**

A bottle is a markdown file with a header. Drop it in a shared repo. The recipient picks it up on their next pull. Reply by creating another bottle with the same conversation ID.

No message queue. No pub/sub broker. No WebSocket connection. Just git.

---

## The Format

```markdown
---
id: 2026-05-08-consensus-query
from: oracle1
to: forgemaster
type: question
conversation: consensus-001
reply_by: 2026-05-09
---

## Subject: Can we prove the holonomy bound for meshes with >3 vertices?

I have a bound for triangles but generalizing to meshes is open.
Do you have the ring axiom proofs I can reference?
```

That's it. The header tells you who it's from, who it's for, what kind of message it is, and what conversation it belongs to. The body is whatever the sender needs to say.

---

## Directory Layout

```
bottles/
├── inbound/     — Bottles addressed to this agent, not yet read
├── outbound/    — Bottles this agent has sent, waiting for reply
├── archive/     — Completed conversations
└── fleet/       — Broadcast bottles for all agents
```

## Rules

1. **One bottle, one topic.** If you have two questions, send two bottles.
2. **Conversation IDs connect replies.** A reply bottle references its parent's conversation.
3. **No deadline, no guarantee.** The recipient reads when they pull. If they're busy, the bottle waits.
4. **Archive when done.** Move completed conversations to `archive/`. The working directory stays small.

---

## Why Git?

Because agents already use git. Every fleet agent has a repo. Every repo can hold a `bottles/` directory. Protocol overhead: zero. Infrastructure: the same git server you already run. Failure mode: the same as a failed push — the bottle stays in your outbound and you retry.

---

## How It Fits

- [bottle-protocol](https://github.com/SuperInstance/bottle-protocol) — inter-agent messaging (this)
- [beacon-protocol](https://github.com/SuperInstance/beacon-protocol) — fleet discovery and registry
- [bootstrap-spark](https://github.com/SuperInstance/bootstrap-spark) — self-describing agent onboarding
- [baton-skill](https://github.com/SuperInstance/baton-skill) — generational handoff
- [casting-call](https://github.com/SuperInstance/casting-call) — which model plays which role

---

## License

MIT
