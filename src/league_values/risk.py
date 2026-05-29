"""Risk / Uncertainty model for dynasty and prospect valuations.

Annotation-only: computes risk metadata alongside existing values.
Does not adjust headline value or ranking order.
"""
from __future__ import annotations

from dataclasses import dataclass


RISK_LEVELS: tuple[tuple[float, str], ...] = (
    (0.25, "Low"),
    (0.50, "Moderate"),
    (0.75, "High"),
    (1.00, "Extreme"),
)


@dataclass(frozen=True)
class RiskDriver:
    """One detected risk factor contributing to a player's risk profile."""
    id: str
    label: str
    score_delta: float
    floor_drag: float
    ceiling_lift: float


@dataclass(frozen=True)
class RiskAssessment:
    """Complete risk annotation for a single player."""
    risk_score: float
    risk_level: str
    value_low: float
    value_high: float
    drivers: tuple[RiskDriver, ...]

    @property
    def driver_labels(self) -> tuple[str, ...]:
        return tuple(d.label for d in self.drivers)

    def to_dict(self) -> dict:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "value_low": self.value_low,
            "value_high": self.value_high,
            "drivers": [d.label for d in self.drivers],
        }
