"""Abstract SQL backend definition — extend by registering a new adapter (open/closed)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class SqlBackendAdapter(ABC):
    """One dialect: schema introspection, read-only execution, Sqlglot + LLM labeling."""

    backend_id: ClassVar[str]
    sqlglot_dialect: ClassVar[str]

    @abstractmethod
    def fetch_schema_metadata(self, connection_url: str) -> dict[str, Any]:
        """Structured tables/columns for UI cache and NL context."""

    @abstractmethod
    def execute_select(
        self, connection_url: str, sql: str
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        """Run a single validated SELECT; return column names and row tuples."""

    def llm_dialect_label(self) -> str:
        """Human name for NL→SQL prompts."""
        return self.backend_id

    def llm_dialect_rules(self) -> str:
        """Extra dialect-specific rules appended to the system prompt."""
        return ""
