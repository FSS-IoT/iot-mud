# IoT MUD Wire Protocol

Version 1. Written 2026-11-19 for the multiplayer slice (M4).

This document is the shared contract between the server and every client. A club
member writes a client from this page alone; server changes are made to keep it
true. Behavior only — no language, no stack. The implementation choice belongs in
the project page, not here.

## Connection

- Transport: WebSocket over plain TCP.
- Endpoint: `ws://<host>:<port>`. The port is an implementation detail, not part
  of the contract — a client should take it from configuration or a discovery
  message, not hardcode it. The reference server listens on **8765** by default;
  the test suite runs servers on other ports (e.g. 8766) so several can run at
  once. `ws://localhost:8765` is given only as a runnable example.
- A client opens one socket, receives the handshake below, and then exchanges
  messages for its whole life.

## Message shape

Every message is a JSON object. Direction is given by the `type` field.

### Server -> client

#### `hello` (handshake)

Sent immediately when a client connects. No input is required to receive it.

| Field | Meaning |
|---|---|
| `v` | Protocol version (`1`). |
| `type` | `"hello"`. |
| `event_id` | Opaque server-side identifier for this message. |
| `seq` | Sequence number assigned by the server (integer). |
| `ts` | Server timestamp in ISO 8601 (`2026-11-14T00:00:00Z`). Informational; clients may ignore it. |
| `data.server` | Server name. |
| `data.protocol` | Supported protocol versions, as a list (`[1]`). |
| `data.auth_required` | Whether future messages require authentication (`false` for now). |
| `data.motd` | Message of the day shown on connect. |

Example:

```json
{
  "v": 1,
  "type": "hello",
  "event_id": "init-1730000000",
  "seq": 1,
  "data": {
    "server": "iot-mud-dev",
    "protocol": [1],
    "auth_required": false,
    "motd": "Welcome to the IoT MUD!"
  }
}
```

#### `command_reply`

Sent in response to a client `input`. Carries the engine's text reply.

| Field | Meaning |
|---|---|
| `v` | Protocol version. |
| `type` | `"command_reply"`. |
| `event_id` | Opaque server-side identifier for this reply. |
| `seq` | Reply sequence number (integer). Equals the request's `id`, so a client can pair replies with requests. |
| `data.text` | The engine's response text. |

### Client -> server

#### `input`

A command from the player to the engine.

| Field | Meaning |
|---|---|
| `v` | Protocol version. |
| `type` | `"input"`. |
| `id` | Client-assigned request id, echoed by the matching reply so a client can pair requests and responses. |
| `data.text` | The raw command string (e.g. `"look"`, `"go north"`, `"take lantern"`). |

Example:

```json
{ "v": 1, "type": "input", "id": 7, "data": { "text": "look" } }
```

## Request / reply pairing

A client sends an `input` with an `id`. The matching `command_reply` returns a
`seq` equal to that `id`, letting a client correlate replies even if messages
arrive out of order. This is the current contract; broadcast events below extend
it without breaking it.

## Events (defined for M4, implemented in later tickets)

The server will push these when the multiplayer slice lands. They are documented
here so clients can be built against them, but they are **not yet sent** — see
issues #22–#24. Each carries a `seq` and lives under its own `type`.

| `type` | Direction | When |
|---|---|---|
| `player_joined` | server -> client | Another player enters the same room. |
| `player_left` | server -> client | A player leaves or disconnects. |
| `room_state` | server -> client | The current room (and its occupants) is sent on join. |

## Invariants

- All messages are JSON. No binary frames.
- The engine is authoritative: clients send intent, the server decides.
- No secrets in the protocol. A connection carries no password for v1
  (`auth_required` is `false`).
