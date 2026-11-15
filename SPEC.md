# Project Specification: IoT MUD

This document defines the architecture, rules, and development lifecycle for the **IoT MUD** project. This is a text-based multiplayer game designed to bridge digital state changes with physical hardware actions via an event-driven architecture.

## 1. The Core Philosophy: Digital Authority
The fundamental principle of this project is **Digital Supremacy**. All gameplay logic resides in the Engine. The AI (Agent) serves as a stylistic interface, not a decision-maker. No matter how much "flavor" an LLM provides, it cannot override the mathematical and logical state managed by the Engine.

## 2. Architecture: The Three Pillars

### 2.1 The Engine (The Law / Deterministic Core)
A local Python `asyncio` server that manages the authoritative state of the world in a SQLite database.
*   **Role:** Validates all actions, calculates math (weight/health), and maintains truth.
*   **Logic Style:** "If-Then-Else" rules based on room tags (`is_climbable`), item properties (`weight`, `portable`), and player stats.
*   **Authority:** If a command is logically impossible according to the data, the Engine rejects it regardless of what an AI agent says.

### 2.2 The Brain (The Describer / LLM Interface)
An LLM-based layer that provides sensory immersion.
*   **Role:** Translates raw engine data into rich, descriptive text and converts natural language input into structured machine commands.
*   **Style Modes:**
    *   **Layer 1 (Describer):** Takes state data $\rightarrow$ outputs beautiful prose.
    *   **Layer 2 (Translator):** Takes natural language ("grab that") $\rightarrow$ outputs intent (`TAKE: item_id`).

### 2.3 The User Interface (The Client)
A client-side implementation (WebSockets/JSON) that renders the text and receives events for potential IoT integration.

---

## 3. Command Processing: The Hybrid Parser
To balance performance with immersion, the system uses a **Cascading Intent Model**:

1.  **The Fast Path (Deterministic):** A regex-based parser handles common commands (`look`, `get <item>`, `n`, `s`) immediately with near-zero latency.
2.  **The Smart Path (Semantic Fallback):** If no fast command matches, the input is routed to an LLM. The AI's job is strictly **Intent Extraction**, reducing complex language into a standardized JSON object: `{ "intent": string, "target": string }`.

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

### Milestone 1: The Pulse (Digital Foundation)
*Goal: A functional, playable digital game with a rock-solid core loop.*
*   **M1-A:** Server Core (Socket connection, Handshake, Auth).
*   **M1-B:** Basic Movement & Room State (navigation between rooms).
*   **M1-C:** Inventory & Weight Logic (portable items, capacity limits).
*   **M1-D:** The Descriptor (Agent provides text for everything in M1).

### Milestone 2: The Soul (World Depth)
*Goal: Increased complexity and "life" in the world.*
*   **M2-A:** NPC Basic Logic (deterministic wandering/dialogue).
*   **M2-B:** Advanced Environmental Rules (climbing, locks, obstacles).
*   **M2-C:** Procedural Content Generation (using AI to generate formatted room data).

### Milestone 3: The Physicality (IoT Bridge)
*Goal: Bridging the digital world to physical hardware.*
*   **M3-A:** Semantic Event Bus (mapping engine events to standard IDs like `light.dim`).
*   **M3-B:** IoT Gateway (MQTT/Webhook integration for external devices).

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
