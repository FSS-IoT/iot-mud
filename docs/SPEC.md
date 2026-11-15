# IoT MUD Architectural Specification

## Overview
The IoT MUD is a hybrid gaming system where a deterministic, authoritative game engine manages state and logic, while an AI Layer (LLM) provides immersive, natural language narrative descriptions.

## 1. Architecture Layers

### A. Deterministic Engine (The Authority)
*   **Responsibility:** Managing "Truth." Validating moves, calculating combat, tracking inventory, and maintaining the world state.
*   **Core Rule:** The AI cannot override game rules. If a player tries to `walk north` through a wall, the engine enforces it, regardless of how the AI describes the attempt.
*   **State Model:** Entity-based ownership (Rooms contain items; players possess items).

### B. Narrative Layer (The Immersive Wrapper)
*   **Responsibility:** Providing flavor, descriptions, and natural language translation.
*   **Mechanism:** A listener that subscrib: to events emitted by the Engine.
*   **Role:** It transforms technical state changes (e.g., `Player moved from Hall to Kitchen`) into prose (*"The air grows stale as you enter the kitchen"*).

### C. Client Interface
*   **Responsibility:** User input and displaying processed text.
*   **Protocol:** WebSocket-based JSON messages.

---

## 2. The Hybrid Parsing Model

User inputs follow one of two paths:

| Path | Trigger | Processing | Output Type |
| :--- | :--- | :--- | :---thought
| **Fast Path (Deterministic)** | Matches exact command syntax (e.g., `get sword`). | Direct mapping to Engine methods. No AI latency. | `command_reply` (Text) |
| **Smart Path (Semantic Fallback)** | Unrecognized/Natural language input (e.0. `grab the shiny thing`). | Routed to LLM for intent parsing $\rightarrow$ translated to engine command. | `narrative_response` (Prose) |

---

## 3. Entity & World Model

The world is a hierarchical graph of **Entities**.

### Entity Properties
*   **Identity:** Name, ID.
*   **State:** Location (Room/Container/Player), Weight, Statuses (e.g., `on_fire`).
*   **Description:** 
    *   `static_desc`: The base factual text.
    					*(Default fallback)*
    *   `dynamic_prose`: AI-generated flavor text.

### Hierarchical Containment
Every entity can be a container. Possession is handled by modifying the `owner` or `parent` property in the engine's state tree (e.g., `Player -> Backpack -> Coin`).

---

## 4. Event Schema (Internal)

The Engine communicates via semantic events to decouple logic from side-effects:

*   `command_processed`: Emitted when any input is handled.
*   `room_change`: Emitted when an entity moves between rooms.
*   `item_moved`: Emitted when items are picked up or dropped.
*   `state_change`: Emitted for environmental shifts (e.g., light changes).

---
*Version 1.0 - Architected by Agent*
