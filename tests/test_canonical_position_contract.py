from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


CANONICAL = load("machine/canonical-position.json")
CAPABILITIES = load("machine/capabilities.json")
TARGET = load("machine/target-contract.json")


class CanonicalPositionContractTests(unittest.TestCase):
    def test_repository_owns_only_exact_contamination_detection(self):
        self.assertEqual(CANONICAL["role"], "CANONICAL_SPECIALIST")
        self.assertEqual(CANONICAL["owns"], "exact_train_eval_contamination_detection")
        self.assertIn("semantic near-duplicate similarity computation", CANONICAL["does_not_own"])
        self.assertIn("label collusion detection", CANONICAL["does_not_own"])
        self.assertIn("annotation budget allocation", CANONICAL["does_not_own"])

    def test_sibling_relationships_do_not_claim_integration(self):
        for edge in CANONICAL["relationships"]:
            self.assertFalse(edge["integration_exercised"])

    def test_capabilities_are_repository_native(self):
        capabilities = set(CAPABILITIES["capabilities"])
        self.assertNotIn("hyper-scaling", capabilities)
        self.assertIn("exact_id_overlap_guard", capabilities)
        self.assertIn("exact_feature_hash_overlap_ratio", capabilities)
        self.assertIn("contamination_policy_fingerprint", capabilities)
        self.assertIn("python_go_contamination_parity", capabilities)

    def test_target_waits_for_exact_head_proof(self):
        self.assertEqual(TARGET["current"]["state"], "PROMOTED")
        self.assertTrue(TARGET["current"]["canonical_position_pending_exact_head_proof"])
        self.assertEqual(TARGET["promotion"]["next_gate"], "CANONICAL_POSITION_RESOLVED")

    def test_truth_boundary_does_not_inflate_hash_equality(self):
        boundary = CAPABILITIES["truth_boundary"]
        self.assertIn("Exact identity/feature-signature", boundary)
        self.assertIn("does not compute semantic near-duplicate similarity", boundary)
        self.assertIn("execute model evaluation", boundary)


if __name__ == "__main__":
    unittest.main()
