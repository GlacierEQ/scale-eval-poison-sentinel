"""Evaluation contamination sentinel — exact identity/feature overlap evidence.

This mechanism detects exact example-ID overlap and exact feature-hash overlap.
A feature hash may represent a similarity bucket produced elsewhere, but this
module does not itself compute semantic or near-duplicate similarity.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Sequence


def digest(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Example:
    example_id: str
    feature_hash: str


@dataclass(frozen=True)
class ContaminationReport:
    id_overlap: int
    feature_overlap: int
    feature_overlap_ratio: float
    train_n: int
    eval_n: int
    contaminated: bool
    input_fingerprint: str
    policy_fingerprint: str
    fingerprint: str


class EvalPoisonSentinel:
    """Fail closed when exact overlap exceeds an explicit bounded policy."""

    def __init__(
        self,
        max_id_overlap: int = 0,
        max_feature_overlap_ratio: float = 0.01,
    ):
        if max_id_overlap < 0:
            raise ValueError("max_id_overlap must be non-negative")
        if (
            not math.isfinite(max_feature_overlap_ratio)
            or not 0.0 <= max_feature_overlap_ratio <= 1.0
        ):
            raise ValueError("max_feature_overlap_ratio must be finite and in [0,1]")
        self.max_id_overlap = max_id_overlap
        self.max_feature_overlap_ratio = max_feature_overlap_ratio

    @staticmethod
    def _validate_dataset(name: str, examples: Sequence[Example]) -> None:
        seen_ids: set[str] = set()
        for example in examples:
            if not example.example_id.strip():
                raise ValueError(f"{name} example_id must be non-empty")
            if not example.feature_hash.strip():
                raise ValueError(f"{name} feature_hash must be non-empty")
            if example.example_id in seen_ids:
                raise ValueError(f"duplicate {name} example_id: {example.example_id}")
            seen_ids.add(example.example_id)

    @staticmethod
    def _dataset_fingerprint(examples: Sequence[Example]) -> list[tuple[str, str]]:
        return sorted((example.example_id, example.feature_hash) for example in examples)

    def analyze(
        self,
        train: Sequence[Example],
        eval_set: Sequence[Example],
    ) -> ContaminationReport:
        self._validate_dataset("train", train)
        self._validate_dataset("eval", eval_set)

        train_ids = {example.example_id for example in train}
        eval_ids = {example.example_id for example in eval_set}
        train_features = {example.feature_hash for example in train}
        eval_features = {example.feature_hash for example in eval_set}

        id_overlap = len(train_ids & eval_ids)
        feature_overlap = len(train_features & eval_features)
        feature_overlap_ratio = feature_overlap / max(len(eval_features), 1)
        contaminated = (
            id_overlap > self.max_id_overlap
            or feature_overlap_ratio > self.max_feature_overlap_ratio
        )

        input_fingerprint = digest(
            {
                "train": self._dataset_fingerprint(train),
                "eval": self._dataset_fingerprint(eval_set),
            }
        )
        policy_fingerprint = digest(
            {
                "max_id_overlap": self.max_id_overlap,
                "max_feature_overlap_ratio": self.max_feature_overlap_ratio,
            }
        )
        report_body = {
            "input_fingerprint": input_fingerprint,
            "policy_fingerprint": policy_fingerprint,
            "id_overlap": id_overlap,
            "feature_overlap": feature_overlap,
            "feature_overlap_ratio": feature_overlap_ratio,
            "train_n": len(train),
            "eval_n": len(eval_set),
            "contaminated": contaminated,
        }
        return ContaminationReport(
            id_overlap=id_overlap,
            feature_overlap=feature_overlap,
            feature_overlap_ratio=feature_overlap_ratio,
            train_n=len(train),
            eval_n=len(eval_set),
            contaminated=contaminated,
            input_fingerprint=input_fingerprint,
            policy_fingerprint=policy_fingerprint,
            fingerprint=digest(report_body),
        )
