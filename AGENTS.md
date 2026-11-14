# Agent Instructions: IoT MUD (Scaffold)

This document provides essential context and standards for agents working in this repository.

## Environment & Standards
- **Runtime**: Python 3.12+
- **Dependency Management**: Use `uv`. Always ensure the environment is synchronized before executing commands (`uv sync`). Avoid installing packages globally.
- **Code Style**: 
  - Strict type hinting for all public functions and class methods.
  - Modular design: Avoid monolithicizing logic in a single file.
  - Asyncio-first: Use `async`/`await` for I/O bound operations.
- **Verification**: Always use `pytest` to verify changes. Do not consider a task complete without passing tests.

## Development Workflow
- **Linting & Formatting**: Prefer `ruff`. Run `uv run ruff check .` and `uv run ruff format .` before committing.
- **Testing**: 
  - Unit tests: `uv run pytest tests/unit`
  - Integration tests: `uv run pytest tests/integration`
- **Execution**: Use `uv run python -m <module_name>` to execute the application or scripts.

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
