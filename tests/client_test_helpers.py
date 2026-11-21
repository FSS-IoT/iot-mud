"""Shared helpers for driving the interactive client in tests."""

import time


def wait_for_output(out, needle: str, timeout: float = 2.0) -> bool:
    """Block until `needle` appears in `out`, or the timeout expires.

    The client renders stream events (the join `room_state`) on the event loop
    while `input()` blocks in a worker thread. Tests that script an immediate
    `exit` therefore race the renderer. Waiting for the output here makes the
    test deterministic without changing the client's behaviour.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if needle in out.getvalue():
            return True
        time.sleep(0.005)
    return False
