# IoT MUD — brief

Written 2026-11-19. Facts carry where they came from. Anything unconfirmed is a
grilling task, not a requirement.

## The idea

One sentence, in Doc's words:

> A multiplayer version of the original Zork — an adventure-style game we can all
> play together online — that doubles as a teaching project for the IoT club, where
> members with little dev experience learn to produce reliable code by working with
> an agentic harness.

## Facts

- **What it is:** A multiplayer text-adventure game (Zork-like feel), not a traditional MUD. Admin/god tasks come from the server interface, not in-game. (source: Doc)
- **Primary purpose:** Teaching members how to interact with an agentic harness to produce reliable code — the fun game is the deliverable, but reliability-through-rigour is the lesson. Members have very little software development experience. (source: Doc)
- **Team model:** Every member writes their own client; some modify server code. The wire protocol is therefore the shared contract that matters most. (source: Doc + existing repo AGENTS.md/SPEC.md)
- **Stack already chosen:** Python 3.12+, `asyncio`, `websockets`, SQLite, `uv`; tests via pytest (TDD red-green), lint with ruff. (source: existing repo pyproject.toml, SPEC.md)
- **Existing work:** A working single-player server exists on GitHub (`FSS-IoT/iot-mud`). Milestone 1 is fully done — connectivity, movement, inventory, nested containers, JSON world loading, an automated end-to-end play test. Milestone 2 prose/descriptor layer is done; natural-language intent extraction and NPCs are not yet started. (source: existing repo SPEC.md + BACKLOG.md)
- **LLM is optional, not core.** The game must run fully standalone/offline on a laptop. LLM only *enhances* room/item descriptions (e.g. brass lantern → elaborately carved prose) and later may drive NPCs. AI integration comes after the playable game; code it with that flexibility in mind. (source: Doc — **corrects the existing SPEC.md, which makes the LLM mandatory**)
- **Taste** (source: Doc): _Like_ — Zork and The Hitchhiker's Guide to the Galaxy, for their prose and parser handling; Mark Twain / Samuel Clemens. _Dislike_ — wandering-around games with nothing to do but talk to other players (no specific title); Shakespeare's writing.
- **How much Zork:** core feel only for v1 — explore, look, carry items. Combat, thieves' guild and treasure scoring are later optional pieces, not in v1. (grill: Doc, 2026-11-19)
- **Parsing:** Zork-style regex parser is primary; the LLM is an optional enhancement that only translates genuinely ambiguous input or adds prose. Cheap and offline-friendly. (grill: Doc, 2026-11-19)
- **Member-authored content:** editing data files (JSON/YAML), not code — like the existing `starting_village.json`. A simple room-generator tool for testing is nice-to-have but low priority and not required. (grill: Doc, 2026-11-19)
- **World content:** reuse the existing `starting_village` JSON world; build new worlds later. (grill: Doc, 2026-11-19)

## Constraints

- Offline-first: a single member must run and play it on one laptop with no internet, no paid APIs, no LLM required. (source: Doc)
- Mixed OS across the team — Windows / Mac / Linux. Setup, tests and protocol must be OS-agnostic and documented for each. (source: Doc)
- Members are beginners: tickets must fit one session, one context window; TDD + review are the point, not ceremony. (source: Doc)
- No secrets in code or vault. (vault contract)

## Non-goals

- **Not a traditional MUD.** No admin commands in-game, no god-mode gameplay. Admin comes from the server interface. (source: Doc)
- **No LLM required to play.** The describer/translator layer is an enhancement, never a dependency for v1. (source: Doc — changes existing spec)
- **Not deep systems work in v1.** Combat, thieves' guild, treasure scoring and other specific Zork mechanics are out — genre and feel only. (source: Doc)
- **No IoT hardware wiring in v1.** Design for it via a clean event bus; do not build the physical bridge yet. (source: Doc)

## Done looks like

- The first version is useful when: one laptop can run the server, two or more clients connect over the network, players see each other in shared rooms, move between rooms, look at rooms and items, take and drop items — all offline, no LLM.
- Desired for v1 (not required to close it): player names + chat channels, so it feels like a real shared space; and member-authored world content tooling (add rooms/items via data files, not code). Both are planned but do not block the first playable version.

## What exists already

- The `FSS-IoT/iot-mud` GitHub repo: working single-player server, tests, a JSON world ("starting village"), specs, backlog. (source: Doc)
- A teaching workflow expectation: red-green TDD with review by a fresh session. (source: existing repo AGENTS.md + software-factory method)
