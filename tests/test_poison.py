from __future__ import annotations
import unittest
from src.poison import EvalPoisonSentinel, Example

class PoisonTests(unittest.TestCase):
    def test_id_overlap(self):
        train = [Example("a", "h1"), Example("b", "h2")]
        ev = [Example("a", "h9")]
        r = EvalPoisonSentinel().analyze(train, ev)
        self.assertTrue(r.contaminated)
        self.assertEqual(r.id_overlap, 1)

    def test_clean(self):
        train = [Example("a", "h1")]
        ev = [Example("c", "h2")]
        r = EvalPoisonSentinel().analyze(train, ev)
        self.assertFalse(r.contaminated)

if __name__ == "__main__":
    unittest.main()
