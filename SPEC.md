# Project Specification: IoT MUD

This document defines the architecture, rules, and development lifecycle for the **IoT MUD** project. This is a text-based multiplayer game designed to bridge digital state changes with physical hardware actions via an event-driven architecture.

---

## Contract

Signed: Doc, 2026-11-19

No code is written before that line exists.

### Scope

A Zork-style text-adventure game that members of the IoT club can all play together online, and that teaches beginners to write reliable code through red-green TDD and review by a fresh session. The deliverable is a fun, playable multiplayer adventure; the method (small tickets, failing check first, review that does not fix) is the lesson. It runs fully offline on one laptop with no LLM required. The shared contract between members is the wire protocol: every member writes their own client, and some edit server code.

v1 layers multiplayer presence onto the existing single-player engine (M1 — movement, inventory, take/drop already work), so v1 is not a blank slate; it connects clients to the authoritative world and makes that world shared.

### Milestones — ticket readiness

| Milestone | What it makes real | Detailed enough for tickets? |
|---|---|---|
| M1 · The Pulse (digital foundation) | Playable single-player core loop | done — no tickets needed |
| M2 · The Soul (world depth) | Natural-language fallback, NPCs, environment rules | grill first |
| M3 · The Physicality (IoT bridge) | Event bus + hardware gateway | designed for, not built |
| **M4 · Multiplayer & Club Content** | Players see each other in a shared world; members author content | **grill first** |

A milestone marked "grill first" gets grilled before it gets tickets. M4 is the v1 priority — its criteria follow. M2 and M3 are real but come after M4 unless Doc says otherwise.

### Acceptance criteria (M4)

- [ ] A server can run on one laptop with no internet and no LLM. (M4)
- [ ] Two clients can connect to the same server over the network. (M4)
- [ ] Players see each other when they are in the same room. (M4)
- [ ] A player moving between rooms updates their position for everyone in the affected rooms. (M4)
- [ ] A player can `look` at a room and its occupants, including other players present. (M4)
- [ ] A player can take an item from a room and drop it again. (M4)
- [ ] The world loads from the existing `starting_village` data file without code changes. (M4)
- [ ] The wire protocol is written down in `docs/PROTOCOL.md` so an independent client can connect. (M4)

### Acceptance criteria (M2 — grill first; not yet actionable)

- [ ] Non-standard input that the regex parser cannot resolve falls back to an LLM for intent extraction only. (M2)
- [ ] NPCs wander and respond deterministically without LLM involvement. (M2)
- [ ] Climbing, locks and obstacles are handled by deterministic engine rules. (M2)

### Acceptance criteria (M3 — designed for, not built; not yet actionable)

- [ ] Engine events map to a semantic event bus with stable IDs (e.g. `light.dim`). (M3)
- [ ] An MQTT/webhook gateway can drive an external device from an engine event. (M3)

### Non-goals

- Not a traditional MUD — no in-game admin/god commands; administration comes from the server interface.
- No LLM required to play. The describer/translator layer is optional and comes after the playable game.
- No deep systems in v1 — combat, thieves' guild, treasure scoring and other specific Zork mechanics are out (genre and feel only).
- No IoT hardware wiring in v1 — designed for via a clean event bus, not built.

### Constraints

- Offline-first: one member runs and plays on a single laptop with no internet, no paid APIs, no LLM required.
- Mixed OS team (Windows / Mac / Linux). Setup, tests and the wire protocol stay OS-agnostic; setup is documented per platform.
- Beginners write the code. Tickets fit one session and one context window; red-green TDD and review by a fresh session are the point, not ceremony.
- No secrets in code or vault.

### Decisions

- 2026-11-19: LLM is optional, not required to play. (page `docs/adr/001-optional-llm.md`)
- 2026-11-19: Regex parser is primary; the LLM translates only genuinely ambiguous input on an opt-in fallback path. (page `docs/adr/002-regex-first-parser.md`)
- 2026-11-19: M4 (multiplayer presence + club content) is v1's priority, ahead of M2 world-depth features. (reason lives in the brief)

### Open questions

- <question>: <who answers it, by when>

### Changes

- 2026-11-19: Spec written from the confirmed brief; LLM corrected from mandatory to optional; M4 added as the v1 milestone.
- 2026-11-19: SPEC.md corrected — LLM changed from mandatory core layer to optional enhancement (grill with Doc).

## 1. The Core Philosophy: Digital Authority
The fundamental principle of this project is **Digital Supremacy**. All gameplay logic resides in the Engine. Any AI (Agent) serves as a stylistic interface, not a decision-maker. No matter how much "flavor" an LLM provides, it cannot override the mathematical and logical state managed by the Engine.

The engine runs **fully offline on one laptop** with no LLM required to play. The LLM layer is optional: it only *enhances* the experience (richer room/item prose, later NPC voices). Code it so the game is complete and playable without it — AI integration comes after the playable game.

## 2. Architecture: The Three Pillars

### 2.1 The Engine (The Law / Deterministic Core)
A local Python `asyncio` server that manages the authoritative state of the world in a SQLite database.
*   **Role:** Validates all actions, calculates math (weight/health), and maintains truth.
*   **Logic Style:** "If-Then-Else" rules based on room tags (`is_climbable`), item properties (`weight`, `portable`), and player stats.
*   **Authority:** If a command is logically impossible according to the data, the Engine rejects it regardless of what an AI agent says.

### 2.2 The Brain (The Optional Describer / LLM Interface)
An optional LLM-based layer that enhances sensory immersion. It is **not required to play** and comes after the playable game; the engine runs fully offline without it.

*   **Role:** Enhances raw engine data into richer, descriptive text, and optionally translates genuinely ambiguous natural language input into structured machine commands (a fallback for when the regex parser cannot resolve intent).
*   **Style Modes:**
    *   **Layer 1 (Describer):** Takes state data $\rightarrow$ outputs elaborately carved prose (e.g. "brass lantern" -> "an intricately carved brass lantern, glass globe stained with soot but still emitting bright light").
    *   **Layer 2 (Translator):** Takes natural language ("grab that") $\rightarrow$ outputs intent (`TAKE: item_id`). Used only on the semantic fallback path; the fast deterministic parser remains primary.
*   The LLM is a thin enhancement over the Engine, never a dependency for v1.

### 2.3 The User Interface (The Client)
A client-side implementation (WebSockets/JSON) that renders the text and receives events for potential IoT integration.

---

## 3. Command Processing: The Hybrid Parser
To balance performance with immersion, the system uses a **Cascading Intent Model**:

1.  **The Fast Path (Deterministic):** A regex-based parser handles common commands (`look`, `get <item>`, `n`, `s`) immediately with near-zero latency. This is the primary interface and works fully offline.
2.  **The Smart Path (Semantic Fallback, optional):** If no fast command matches *and an LLM layer is enabled*, the input is routed to the LLM for intent extraction only — reducing complex language into a standardized JSON object: `{ "intent": string, "target": string }`. The AI's job is strictly **Intent Extraction**; it never overrides the Engine.
3.  **No match (no LLM):** If no fast command matches and the LLM layer is disabled, the Engine reports an unrecognized command. No fallback is invented — the game remains fully playable offline.

---

## 4. Memory Architecture: Three-Tiered Context
To prevent LLM context bloat and ensure long-term world consistency, memory is tiered:

| Tier | Name | Technical Implementation | Purpose for AI Agent |
| :--- | :--- | :--- | :--- |
| **Tier 1** | **Immediate Echo** | SQLite `event_log` (Last ~20 rows) | Real-time situational awareness. |
| **Tier 2** | **World Snapshot** | Primary Relational Tables (`players`, `rooms`) | The "absolute truth" of current state. |
| **Tier 3** | **Grand Legend** | SQLite `world_lore` (Summaries) | Long-term historical/narrative context. |

---

## 5. Implementation Milestones

### Milestone 1: The Pulse (Digital Foundation) — *DONE*
*Goal: A functional, playable digital game with a rock-solid core loop.*
*   **M1-A:** Server Core (Socket connection, Handshake, Auth). `[x]`
*   **M1-B:** Basic Movement & Room State (navigation between rooms). `[x]`
*   **M1-C:** Inventory & Weight Logic (portable items, capacity limits). `[x]`
*   **M1-D:** The Descriptor (Agent provides text for everything in M1). `[x]`

### Milestone 2: The Soul (World Depth)
*Goal: Increased complexity and "life" in the world.*
*   **M2-A:** Natural-language intent extraction (semantic fallback, optional LLM layer). `[ ]` — this is where the current spec's unfinished work lives.
*   **M2-B:** NPC Basic Logic (deterministic wandering/dialogue). `[ ]`
*   **M2-C:** Advanced Environmental Rules (climbing, locks, obstacles). `[ ]`
*   **M2-D:** Procedural Content Generation (optional: using AI to generate formatted room data). `[ ]`

### Milestone 3: The Physicality (IoT Bridge) — *DESIGNED FOR, NOT BUILT*
*Goal: Bridging the digital world to physical hardware. Design for it via a clean event bus; do not build the physical bridge in v1.*
*   **M3-A:** Semantic Event Bus (mapping engine events to standard IDs like `light.dim`). `[ ]`
*   **M3-B:** IoT Gateway (MQTT/Webhook integration for external devices). `[ ]`

### Milestone 4: Multiplayer & Club Content *(new, per the brief)*
*Goal: The Zork-like game that members can all play together and help build.*
*   **M4-A:** Presence + shared world — players see each other in shared rooms, move, look, take/drop items together. Offline-capable. `[ ]`
*   **M4-B:** Player names + chat channels (shared space). `[ ]`
*   **M4-C:** Member-authored content: add rooms/items by editing data files (JSON/YAML), not code. `[ ]`
*   **M4-D:** Simple room-generator tool for testing. `[ ]` — nice-to-have, low priority.

---

## 6. Development Standards

### 6.1 Testing Methodology: Red-Green-Refactor
Every feature must be implemented via Test-Driven Development (TDD):
1.  **RED:** Write a test that expects the new behavior and observe it fail.
2.  **GREEN:** Write the minimum amount of code required to make the test pass.
3.  **REFACTOR:** Clean up the implementation while ensuring tests remain green.

### 6.2 Toolchain & Workflow
*   **Language:** Python 3.12+ (Async/Await focus).
*   **Environment/Deps:** `uv` (Strictly enforced; no global installs).
*   **Linting/Formatting:** `ruff`.
*   **Testing Framework:** `pytest` with `pytest-asyncio`.
*   **Version Control:** Git. Every commit must be atomic and self-documenting.

---
