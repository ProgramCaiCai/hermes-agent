"""Backward-compatible built-in memory provider shim."""

from __future__ import annotations

import json

from agent.memory_provider import MemoryProvider


class BuiltinMemoryProvider(MemoryProvider):
    """Minimal builtin provider used for manager wiring and compatibility."""

    @property
    def name(self) -> str:
        return "builtin"

    def is_available(self) -> bool:
        return True

    def initialize(self, session_id: str, **kwargs) -> None:
        return None

    def system_prompt_block(self) -> str:
        return ""

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        return ""

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        return None

    def get_tool_schemas(self):
        return []

    def handle_tool_call(self, tool_name, args, **kwargs):
        return json.dumps({})

    def shutdown(self) -> None:
        return None
