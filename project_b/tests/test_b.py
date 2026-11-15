import unittest, numpy as np
from project_b.synth_311 import synth
from project_b.injector import inject, PTYPES
from project_b.detectors import rules, stats
from project_b.detectors.base import Reference


class TestB(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = synth(40000, seed=3); cls.ref = Reference().fit(cls.df.iloc[:30000]); cls.clean = cls.df.iloc[30000:35000].reset_index(drop=True)

    def test_injector_changes_data_and_truth_matches(self):
        rng = np.random.default_rng(0)
        for p in PTYPES:
            c, t = inject(self.clean, p, .05, rng)
            self.assertFalse(c.equals(self.clean), p)
            if t["rows"] is not None:
                self.assertEqual(len(t["rows"]), len(c)); self.assertGreater(t["rows"].sum(), 0, p)

    def test_rules_flag_corruption_not_clean(self):
        rng = np.random.default_rng(1)
        for p in ("schema", "dtype", "datefmt", "latlon", "dup", "closed_before", "zipboro", "pair", "resolution"):
            a = rules.DETECTORS[p](inject(self.clean, p, .05, rng)[0], self.ref)
            got = a.flag if a.flag is not None else a.mask.sum() > 20
            self.assertTrue(got, p)
            a0 = rules.DETECTORS[p](self.clean, self.ref)
            self.assertFalse(a0.flag if a0.flag is not None else a0.mask.sum() > 20, p)

    def test_stats_nullspike_beats_required_col_rule(self):
        rng = np.random.default_rng(2); hits = 0
        for _ in range(8):
            c, _t = inject(self.clean, "nullspike", .05, rng); hits += bool(stats.DETECTORS["nullspike"](c, self.ref).flag)
        self.assertGreaterEqual(hits, 7)


if __name__ == "__main__":
    unittest.main()
