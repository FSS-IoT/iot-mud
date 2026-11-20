# Project Backlog (Issue Tracker)

This document tracks all planned features, tasks, and bugs. Every task follows a **Red-Green** lifecycle. 

Dependencies are explicitly listed to prevent agents from working on unblocked tasks.

## Legend
- [ ] `TODO`: Not started.
- [/] `IN_PROGRESS`: Currently being worked on by the Lead Developer or Subagent.
- [x] `DONE`: Passed Red Phase, implementation is complete and verified.
- [!] `BLOCKED`: Waiting for clarification or higher-level design decision.

---



## Milestone 1: The Pulse (Digital Core)
*Goal: Establishing connectivity, command parsing, and the fundamental object model.*

### M1-A: Connectivity & Lifecycle
- [x] **[TASK-001] Red: Connectivity Failure** - *Write a test that fails when attempting to connect to an inactive server.*
- [x] **[TASK-002] Green: Server Handshake** (Prereq: TASK-001) - *Implement basic WebSocket server and "hello" handshake logic.*
- [x] **[TASK-003] Red: Lifecycle Management** (Prereq: TASK-002) - *Ensure clean shutdown of the server on interrupt/signal.*

### M1-B: The Core Engine & State Transition
- [x] **[TASK-004] Red: Command Input Test** (Prereq: TASK-003) - *Test that receiving an "input" message triggers a backend command.*
- [x] **[TASK-005] Green: Command Routing** (Prereq: TASK-004) - *Implement the core loop to receive packets and route them through the engine.*
- [x] **[TASK-006] Refactor: Engine Integration** (Prereq: TASK-005) - *Decouple networking from logic; implement the base Engine class.*

### M1-C: The Hybrid Parser (Translator & Fast Path)
- [x] **[TASK-007] Red: Deterministic Input Test** (Prereq: TASK-006) - *Verify that 'get sword' is treated as 'take {sword}' correctly without LLM help.*
- [x] **[TASK-008] Green: Semantic Fallback** (Prereq: TASK-007) - *Integrate the AI/Mock Agent to handle non-standard natural language inputs.*

### M1-D: The Interactive World (Entity & Space)
- [x] **[TASK-009] Red/Green: Entity Model** — *Implement a base `Entity` class with properties (name, desc, weight).*
- [x] **[TASK-010] Red/Green: Spatial Graph** — *Define 'Rooms' as containers that hold entities and handle exits.*
- [x] **[TASK-011] Red/Green: Basic Inventory** — *Logic for player "taking" and "dropping" items via parent/child updates.*
- [x] **[TASK-012] Red/Green: Nested Containers** — *Implement hierarchical containment (e.g., item in chest).*

### M1-E: World Loading & Bootstrapping
- [x] **[TASK-013] Red/Green: Void World Verification** — *Confirm a fresh engine instance initializes with no default objects.*
- [x] **[TASK-014] Green: The "First Village" Loader** — *Implement loading logic to populate the engine with a predefined graph of 5+ rooms and items.*
- [x] **[TASK-015] Refactor: Data-Driven Worlds** — *Extract world layout into external config files (JSON) to separate logic from content.*

### M1-F: End-to-End Playability
*Goal: Verifying the system as a seamless integrated product via simulated clients.*
- [x] **[TASK-016] Red/Green: Protocol Handshake Automation** — *Verify that an automated client can successfully complete the WebSocket handshake.*
- [x] **[TASK-017] Red/Green: Automated Play Session** — *Run a complete script: Connect $\rightarrow$ Look $\rightarrow$ Move $\rightarrow$ Take $\rightarrow$ Drop $\rightarrow$ Disconnect.*
- [x] **[TASK-018] Refactor: Command Concurrency** — *Ensure WebSocket messages arrive and process in the correct chronological sequence.*

---



## Milestone 2: Deepening Intelligence
### M2-A: The Descriptor Layer (AI Prose)
- [x] **[TASK-019] Red: Prose Test** (Prereq: TASK-018) — *Ensure state changes trigger semantic event hooks for descriptive narration.*
- [x] **[TASK-020] Green: Descriptive Narrative** (Prereq: TASK-019) — *Integrate the Agent as the primary descriptor for game entities.*
- [x] **[TASK-021] Implementation: Environment Auto-Perception** — *Automatically show room description and exits upon entry.*
- [x] **[TASK-022] Feature: UI Cleanliness** — *Reduce logging noise so only game prose reaches the terminal.*
- [x] **[TASK-023] Implementation: Command Priority Hierarchy** — *Handle system signals (`exit`) before gameplay commands (`exits`).*

### M2-B: Cognitive Expansion
- [ ] **[TASK-024] Feature: Natural Language Intent Extraction** — *Leverage LLMs to convert ambiguous user input into executable actions.*
- [ ] **[TASK-025] Feature: Persistent NPC Awareness** — *Enable NPCs to react dynamically to player movements and verbalization.*

### M2-C: Demo Readiness (Playtesting Bugfix)
- [x] **[TASK-026] Fix: Login Blank + Movement Duplication** — *On login the starting room never rendered; on move the room was described twice (once with items, once without). Made the `go` reply the single source of truth for arrival (engine `_describe_movement` now lists destination contents), removed the server's redundant mover `room_state` push, and split the client into live stream events vs. matched replies so the join view renders immediately instead of buffering behind the first command.*

---

*Generated by Lead Developer (Agent)*
