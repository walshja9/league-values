"""Tests for the Risk/Uncertainty model."""

import unittest
from types import SimpleNamespace

from league_values.risk import (
    RiskDriver,
    RiskAssessment,
    RISK_LEVELS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mlb_row(**kwargs):
    defaults = dict(
        player_type="mlb", positions=("OF",), age=28, dynasty_value=80.0,
        eta=None, level=None, source_ranks=None, breakout_label=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _prospect_row(**kwargs):
    defaults = dict(
        player_type="prospect", positions=("SS",), age=20, dynasty_value=50.0,
        eta=2028, level="AA", source_ranks={"pipeline": 30, "hkb": 45},
        breakout_label=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# Task 1: Core types
# ---------------------------------------------------------------------------

class TestRiskDriver(unittest.TestCase):

    def test_frozen_dataclass(self):
        d = RiskDriver("test_id", "Test Label", 0.10, 5.0, 3.0)
        self.assertEqual(d.id, "test_id")
        self.assertEqual(d.label, "Test Label")
        self.assertEqual(d.score_delta, 0.10)
        self.assertEqual(d.floor_drag, 5.0)
        self.assertEqual(d.ceiling_lift, 3.0)

    def test_immutable(self):
        d = RiskDriver("id", "Label", 0.05, 2.0, 1.0)
        with self.assertRaises(Exception):
            d.id = "new_id"  # type: ignore[misc]

    def test_equality(self):
        d1 = RiskDriver("a", "A", 0.1, 1.0, 2.0)
        d2 = RiskDriver("a", "A", 0.1, 1.0, 2.0)
        self.assertEqual(d1, d2)


class TestRiskAssessment(unittest.TestCase):

    def _make(self, drivers=()):
        return RiskAssessment(
            risk_score=0.30,
            risk_level="Moderate",
            value_low=45.0,
            value_high=65.0,
            drivers=tuple(drivers),
        )

    def test_frozen(self):
        ra = self._make()
        with self.assertRaises(Exception):
            ra.risk_score = 0.99  # type: ignore[misc]

    def test_driver_labels_empty(self):
        ra = self._make()
        self.assertEqual(ra.driver_labels, ())

    def test_driver_labels(self):
        d1 = RiskDriver("a", "Alpha", 0.05, 1, 1)
        d2 = RiskDriver("b", "Beta", 0.05, 1, 1)
        ra = self._make(drivers=(d1, d2))
        self.assertEqual(ra.driver_labels, ("Alpha", "Beta"))

    def test_to_dict_keys(self):
        ra = self._make()
        d = ra.to_dict()
        self.assertIn("risk_score", d)
        self.assertIn("risk_level", d)
        self.assertIn("value_low", d)
        self.assertIn("value_high", d)
        self.assertIn("drivers", d)

    def test_to_dict_drivers_list_of_labels(self):
        d1 = RiskDriver("x", "X Label", 0.01, 1, 1)
        ra = self._make(drivers=(d1,))
        result = ra.to_dict()
        self.assertEqual(result["drivers"], ["X Label"])

    def test_to_dict_values(self):
        ra = self._make()
        d = ra.to_dict()
        self.assertEqual(d["risk_score"], 0.30)
        self.assertEqual(d["risk_level"], "Moderate")
        self.assertEqual(d["value_low"], 45.0)
        self.assertEqual(d["value_high"], 65.0)


class TestRiskLevels(unittest.TestCase):

    def test_is_tuple(self):
        self.assertIsInstance(RISK_LEVELS, tuple)

    def test_four_entries(self):
        self.assertEqual(len(RISK_LEVELS), 4)

    def test_ascending_thresholds(self):
        thresholds = [t for t, _ in RISK_LEVELS]
        self.assertEqual(thresholds, sorted(thresholds))

    def test_top_threshold_is_one(self):
        self.assertEqual(RISK_LEVELS[-1][0], 1.00)

    def test_level_names(self):
        names = [n for _, n in RISK_LEVELS]
        self.assertIn("Low", names)
        self.assertIn("Moderate", names)
        self.assertIn("High", names)
        self.assertIn("Extreme", names)


if __name__ == "__main__":
    unittest.main()
