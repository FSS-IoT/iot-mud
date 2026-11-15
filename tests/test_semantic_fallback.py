import pytest
import asyncio
from src.mud.engine.core import Engine

@pytest.mark.asyncio
async def test_semantic_fallback_red():
    """[TASK-008] RED PHASE: Verify that unhandled commands trigger the semantic fallback mechanism."""
    engine = Engine()
    
    # A command that currently doesn't match any deterministic rule
    unrecognized_command = "dance wildly in a circle"
    
    result = await engine.process_command(unrecognized_command)
    
    # Our current implementation returns: f"I don't understand '{command_text}'."
    # For TASK-008, we want it to return something that indicates an AI fallback is triggered 
    # or at least specifically identifies it as unrecognized for semantic processing.
    
    assert "AI searching" in result or result == "[FALLBACK]" # This will fail with current implementation
