import unittest
from dataclasses import fields
from ground_pathway_poc.engine import HazardSet, propagate, compose_external_mov0


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.h = HazardSet(.0002, .001, .0015, .0003, .0001, .0002, .0004, .003, .004)

    def test_mass(self):
        x = propagate(self.h)
        self.assertAlmostEqual(sum(x.values()), 1)
        self.assertGreater(x["submission"], 0)

    def test_no_hazards_is_decision(self):
        self.assertEqual(propagate(HazardSet(*([0.] * 9))), {
            "ko": 0., "submission": 0., "decision": 1.})

    def test_swap(self):
        h = self.h
        swapped = HazardSet(h.standing_ko, h.enter_ground_b, h.enter_ground_a,
                            h.ground_ko_b, h.ground_ko_a,
                            h.ground_sub_b, h.ground_sub_a, h.return_b, h.return_a)
        x, y = propagate(h), propagate(swapped)
        for k in x:
            self.assertAlmostEqual(x[k], y[k], places=12)

    def test_reject_invalid(self):
        h = HazardSet(-.1, *([0.] * 8))
        with self.assertRaises(ValueError):
            propagate(h)
        with self.assertRaises(ValueError):
            propagate(self.h, step_seconds=7)

    def test_step_convergence(self):
        a = propagate(self.h, step_seconds=1)
        b = propagate(self.h, step_seconds=5)
        for k in a:
            self.assertLess(abs(a[k] - b[k]), .01)

    def test_external_composition(self):
        self.assertEqual(compose_external_mov0(.6, .7),
                         {"ko": .42, "submission": .18, "decision": .4})


if __name__ == "__main__":
    unittest.main()
