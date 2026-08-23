from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import unittest

from ufc_edge.features.materializer import MaterializerError, V1Materializer


ROOT = Path(__file__).resolve().parents[2]


class TargetRequestGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.materializer = V1Materializer(ROOT)
        cls.store = cls.materializer.store
        cls.fights = sorted(
            cls.store.fights.values(),
            key=lambda fight: (fight.event_date, fight.fight_id),
            reverse=True,
        )
        cls.target = cls.fights[0]
        cls.same_day_cutoff = f"{cls.target.event_date.isoformat()}T12:00:00Z"
        cls.after_cutoff = f"{(cls.target.event_date + timedelta(days=1)).isoformat()}T00:00:00Z"

    def test_same_day_target_materialization_remains_valid(self) -> None:
        fighter = self.materializer.materialize_fighter(
            self.target.fighter_a_id,
            self.same_day_cutoff,
            target_fight_id=self.target.fight_id,
        )
        matchup = self.materializer.materialize_matchup(
            self.target.fighter_a_id,
            self.target.fighter_b_id,
            self.same_day_cutoff,
            target_fight_id=self.target.fight_id,
        )
        self.assertEqual(fighter.target_fight_id, self.target.fight_id)
        self.assertEqual(matchup.target_fight_id, self.target.fight_id)

    def test_cutoff_after_target_date_is_rejected(self) -> None:
        with self.assertRaisesRegex(MaterializerError, "is historical"):
            self.materializer.materialize_fighter(
                self.target.fighter_a_id,
                self.after_cutoff,
                target_fight_id=self.target.fight_id,
            )
        with self.assertRaisesRegex(MaterializerError, "is historical"):
            self.materializer.materialize_matchup(
                self.target.fighter_a_id,
                self.target.fighter_b_id,
                self.after_cutoff,
                target_fight_id=self.target.fight_id,
            )

    def test_bad_cutoff_cannot_feed_target_into_historical_lineage(self) -> None:
        # This proves the underlying date-only history rule would classify the
        # target as prior history at the bad cutoff, while the public API rejects
        # the request before state/sufficient-stat construction can occur.
        raw_prior = self.store.prior_fights(self.target.fighter_a_id, self.after_cutoff)
        self.assertIn(self.target.fight_id, {fight.fight_id for fight in raw_prior})
        with self.assertRaises(MaterializerError):
            self.materializer.materialize_fighter(
                self.target.fighter_a_id,
                self.after_cutoff,
                target_fight_id=self.target.fight_id,
                consumer="model0",
            )

    def test_unrelated_target_is_rejected_independent_of_consumer_projection(self) -> None:
        unrelated = next(
            fight
            for fight in self.fights[1:]
            if self.target.fighter_a_id not in {fight.fighter_a_id, fight.fighter_b_id}
        )
        cutoff = f"{unrelated.event_date.isoformat()}T12:00:00Z"
        with self.assertRaisesRegex(MaterializerError, "does not include requested fighter"):
            self.materializer.materialize_fighter(
                self.target.fighter_a_id,
                cutoff,
                target_fight_id=unrelated.fight_id,
                consumer="component_striking",
            )

    def test_matchup_rejects_target_missing_either_requested_fighter(self) -> None:
        unrelated = next(
            fight
            for fight in self.fights[1:]
            if self.target.fighter_a_id not in {fight.fighter_a_id, fight.fighter_b_id}
        )
        cutoff = f"{unrelated.event_date.isoformat()}T12:00:00Z"
        with self.assertRaisesRegex(MaterializerError, "does not include requested fighter"):
            self.materializer.materialize_matchup(
                unrelated.fighter_a_id,
                self.target.fighter_a_id,
                cutoff,
                target_fight_id=unrelated.fight_id,
                consumer="component_striking",
            )


if __name__ == "__main__":
    unittest.main()
