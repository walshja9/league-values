from __future__ import annotations

from typing import Protocol, runtime_checkable

from .models import LeagueConfig, ValuationResult


@runtime_checkable
class PostProcessor(Protocol):
    def process(
        self,
        results: list[ValuationResult],
        league: LeagueConfig,
    ) -> list[ValuationResult]: ...
