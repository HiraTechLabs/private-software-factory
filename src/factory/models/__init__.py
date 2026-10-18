"""Model gateway package: the three roles share one ask() interface."""

from __future__ import annotations

from factory.models.gateway import Answer, ManualAnswerRequired, ask, test_provider

__all__ = ["Answer", "ManualAnswerRequired", "ask", "test_provider"]
