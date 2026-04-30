import queue
from unittest.mock import AsyncMock

import pytest

from gateway.config import Platform
from gateway.platforms.base import MessageEvent, MessageType
from gateway.run import GatewayRunner
from gateway.session import SessionSource


def _event(*, internal=False, raw_message=None):
    return MessageEvent(
        text="hello",
        message_type=MessageType.TEXT,
        source=SessionSource(
            platform=Platform.TELEGRAM,
            chat_id="chat-1",
            user_id="user-1",
        ),
        raw_message=raw_message,
        internal=internal,
    )


class _FakeRegistry:
    def __init__(self, events):
        self.completion_queue = queue.Queue()
        for event in events:
            self.completion_queue.put(event)


@pytest.mark.asyncio
async def test_watch_drain_coalesces_same_process_events(monkeypatch):
    import tools.process_registry as process_registry_module

    registry = _FakeRegistry([
        {
            "type": "watch_match",
            "session_id": "proc_same",
            "command": "tail -f app.log",
            "pattern": "error",
            "output": "error one",
        },
        {
            "type": "watch_match",
            "session_id": "proc_same",
            "command": "tail -f app.log",
            "pattern": "error",
            "output": "error two",
        },
    ])
    monkeypatch.setattr(process_registry_module, "process_registry", registry)

    runner = GatewayRunner.__new__(GatewayRunner)
    runner._inject_watch_notification = AsyncMock()

    await runner._drain_watch_notifications(_event())

    runner._inject_watch_notification.assert_awaited_once()
    synth_text = runner._inject_watch_notification.await_args.args[0]
    assert "error two" in synth_text
    assert "additional watch matches were coalesced" in synth_text


@pytest.mark.asyncio
async def test_watch_drain_uses_single_synthetic_message_for_batch(monkeypatch):
    import tools.process_registry as process_registry_module

    registry = _FakeRegistry([
        {
            "type": "watch_match",
            "session_id": "proc_one",
            "command": "cmd one",
            "pattern": "error",
            "output": "error one",
        },
        {
            "type": "watch_match",
            "session_id": "proc_two",
            "command": "cmd two",
            "pattern": "panic",
            "output": "panic two",
        },
    ])
    monkeypatch.setattr(process_registry_module, "process_registry", registry)

    runner = GatewayRunner.__new__(GatewayRunner)
    runner._inject_watch_notification = AsyncMock()

    await runner._drain_watch_notifications(_event())

    runner._inject_watch_notification.assert_awaited_once()
    synth_text = runner._inject_watch_notification.await_args.args[0]
    assert "proc_one" in synth_text
    assert "proc_two" in synth_text


@pytest.mark.asyncio
async def test_synthetic_watch_event_does_not_drain_watch_queue(monkeypatch):
    import tools.process_registry as process_registry_module

    registry = _FakeRegistry([
        {
            "type": "watch_match",
            "session_id": "proc_recursive",
            "command": "tail -f app.log",
            "pattern": "error",
            "output": "error loop",
        }
    ])
    monkeypatch.setattr(process_registry_module, "process_registry", registry)

    runner = GatewayRunner.__new__(GatewayRunner)
    runner._inject_watch_notification = AsyncMock()

    await runner._drain_watch_notifications(
        _event(
            internal=True,
            raw_message={"gateway_internal_kind": "watch_notification"},
        )
    )

    runner._inject_watch_notification.assert_not_awaited()
    assert registry.completion_queue.qsize() == 1


@pytest.mark.asyncio
async def test_injected_watch_notification_marks_internal_kind():
    class Adapter:
        def __init__(self):
            self.events = []

        async def handle_message(self, event):
            self.events.append(event)

    adapter = Adapter()
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.adapters = {Platform.TELEGRAM: adapter}

    await runner._inject_watch_notification("[SYSTEM: watch]", _event())

    assert len(adapter.events) == 1
    synth_event = adapter.events[0]
    assert synth_event.internal is True
    assert synth_event.raw_message == {"gateway_internal_kind": "watch_notification"}
