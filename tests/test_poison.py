from __future__ import annotations

import math
import unittest

from src.poison import EvalPoisonSentinel, Example


class PoisonTests(unittest.TestCase):
    def test_id_overlap(self):
        train = [Example("a", "h1"), Example("b", "h2")]
        eval_set = [Example("a", "h9")]
        report = EvalPoisonSentinel().analyze(train, eval_set)
        self.assertTrue(report.contaminated)
        self.assertEqual(report.id_overlap, 1)

    def test_feature_hash_overlap_reports_ratio(self):
        train = [Example("a", "h1"), Example("b", "h2")]
        eval_set = [Example("c", "h1"), Example("d", "h3")]
        report = EvalPoisonSentinel(max_feature_overlap_ratio=0.4).analyze(
            train, eval_set
        )
        self.assertEqual(report.feature_overlap, 1)
        self.assertEqual(report.feature_overlap_ratio, 0.5)
        self.assertTrue(report.contaminated)

    def test_clean(self):
        train = [Example("a", "h1")]
        eval_set = [Example("c", "h2")]
        report = EvalPoisonSentinel().analyze(train, eval_set)
        self.assertFalse(report.contaminated)

    def test_policy_threshold_is_bound_into_receipt(self):
        train = [Example("a", "h1")]
        eval_set = [Example("c", "h1")]
        strict = EvalPoisonSentinel(max_feature_overlap_ratio=0.0).analyze(
            train, eval_set
        )
        permissive = EvalPoisonSentinel(max_feature_overlap_ratio=1.0).analyze(
            train, eval_set
        )
        self.assertNotEqual(strict.policy_fingerprint, permissive.policy_fingerprint)
        self.assertNotEqual(strict.fingerprint, permissive.fingerprint)
        self.assertTrue(strict.contaminated)
        self.assertFalse(permissive.contaminated)

    def test_input_identity_is_bound_into_receipt(self):
        first = EvalPoisonSentinel().analyze(
            [Example("a", "h1")], [Example("b", "h2")]
        )
        second = EvalPoisonSentinel().analyze(
            [Example("x", "h1")], [Example("y", "h2")]
        )
        self.assertNotEqual(first.input_fingerprint, second.input_fingerprint)
        self.assertNotEqual(first.fingerprint, second.fingerprint)

    def test_duplicate_ids_refuse(self):
        with self.assertRaisesRegex(ValueError, "duplicate train example_id"):
            EvalPoisonSentinel().analyze(
                [Example("a", "h1"), Example("a", "h2")],
                [Example("b", "h3")],
            )

    def test_empty_identity_or_feature_refuses(self):
        with self.assertRaises(ValueError):
            EvalPoisonSentinel().analyze([Example("", "h1")], [])
        with self.assertRaises(ValueError):
            EvalPoisonSentinel().analyze([Example("a", "")], [])

    def test_invalid_policy_refuses(self):
        with self.assertRaises(ValueError):
            EvalPoisonSentinel(max_id_overlap=-1)
        for value in (-0.1, 1.1, math.inf, math.nan):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    EvalPoisonSentinel(max_feature_overlap_ratio=value)


if __name__ == "__main__":
    unittest.main()
