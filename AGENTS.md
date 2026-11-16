# Agent Instructions: IoT MUD (Scaffold)

This document provides essential context and standards for agents working in this repository.

## Environment & Standards
- **Runtime**: Python 3.12+
- **Dependency Management**: Use `uv`(or venv if uv is not installed). Always ensure the environment is synchronized before executing commands (`uv sync`). Avoid installing packages globally.
- **Code Style**: 
  - Strict type hinting for all public functions and class methods.
  - Modular design: Avoid monolithicizing logic in a single file.
  - Asyncio-first: Use `async`/`await` for I/O bound operations.
- **Verification**: Always use `pytest` to verify changes. Do not consider a task complete without passing tests.

## Agentic Orchestration & Workflow

### Task Execution Model (Red-Green)
This repository strictly adheres to a **Test-Driven Development (TDD)** lifecycle for all new features and bug fixes:
1.  **RED PHASE:** Write a failing test that defines the desired behavior. A task is only considered "started" once this failure is verified.
2.  **GREEN PHASE:** Implement the minimum code required to make the test pass.
3.  **REFACTOR/DONE Phase:** Clean the code and mark the task as `[x] DONE` in the `BACKLOG.md`.

### Subagent Orchestration & Dependency Management
To prevent wasted compute and context fragmentation, agents must follow these orchestration rules:

1.  **Dependency Gatekeeping:** Before spawning a subagent or starting work on a new task, check `BACKLOG.md`. If the current task has prerequisite tasks that are not marked as `[x] DONE`, **STOP**. The agent is blocked and cannot proceed until dependencies are completed.
2.  **Sequential Milestone Progression:** Subagents should generally be assigned to a single task within an active milestone. Do not attempt to parallelize subagents across different milestones unless it is explicitly authorized by the Lead Developer in conversation.
3.g **Contextual Awareness:** When spawned, a subagent must be aware of its specific scope (e.g., "You are working on TASK-005, do not touch Task 002").

### Communication & Accountability
*   **Progress Tracking:** Every task completed or failed must be reflected in the `BACKLOG.md`.
*   **Task Identification:** All commits and communications should reference the specific **[TASK-XXXX]** ID being addressed.

## Architecture Principles (Intended)
*Note: These are guiding principles for the upcoming implementation phase.*

- **State Integrity**: All mutations must be atomic and persistent. High priority on "write-through" patterns to database/storage before updating in-memory state.
- **Event-Driven Communication**: Use an internal event bus for decoupling core logic from side effects (e.g., networking, logging, hardware bridges).
- **Deterministic Core**: Avoid using `random` or wall-clock time directly in business logic; use seeded RNGs and controlled clock injection to ensure reproducible tests/simulations.

## Critical Commands (Scaffold)
| Action | Command |
| :--- | :--- |
| Initialize Environment | `uv sync` |
| Run Application | `uv run python -m src.<module>` |
| Run All Tests | `uv run pytest` |
| Check Linting | `uv run ruff check .` |
| Format Code | `uv run ruff format .` |

## Important Resources (To be populated)
- `docs/ARCHITECTURE.md`: High-level system design and data models.
- `docs/PROTOCOL.md`: Definition of the wire protocol for clients.
- `CONTRIBUTING.md`: Project-specific workflow and branching rules.
