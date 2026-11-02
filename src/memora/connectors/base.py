from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentEvent:
    agent: str
    content: str
    event_type: str = "note"
    project: str | None = None
    external_session_id: str | None = None
    metadata: dict[str, Any] | None = None


class AgentConnector(ABC):
    """Contract implemented by native agent integrations."""

    name: str
    capabilities: set[str] = set()

    @abstractmethod
    async def install(self) -> None:
        """Install or configure the integration with explicit user consent."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return whether the integration can communicate with its agent."""
