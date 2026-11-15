import pytest
from src.mud.engine.core import Engine

@pytest.mark.asyncio
async def test_deterministic_parsing():
    """[TASK-007] RED PHASE: Verify that specific syntax is handled deterministically."""
    engine = Engine()
    
    # In the future, we'll have a more sophisticated parser inside process_command.
    # For now, this should probably return something or at least show it can handle multi-word commands.
    result = await engine.process_command("say hello world")
    assert result == 'You say, "hello world"'

@pytest.mark.asyncio
async def test_command_alias_deterministic():
    """[TASK-007] RED PHASE: Verify command aliases like 'get' -> 'take'."""
    engine = Engine()
    # We want to ensure that if we say "get sword", it works correctly in the future.
    # Currently, our simple engine doesn't have an alias map (Requirement for TASK-007).
    result = await engine.process_command("get sword")
    
    # This is expected to fail or return a default error currently because our logic only handles 'say', 'look', etc.
    assert "You take sword" in result or "take sword" in result.lower()
