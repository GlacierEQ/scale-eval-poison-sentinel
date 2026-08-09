"""Eval poison sentinel — train/eval contamination detector."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Sequence


def digest(obj: object) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class Example:
    example_id: str
    feature_hash: str


@dataclass(frozen=True)
class ContaminationReport:
    id_overlap: int
    feature_overlap: int
    train_n: int
    eval_n: int
    contaminated: bool
    fingerprint: str


class EvalPoisonSentinel:
    def __init__(self, max_id_overlap: int = 0, max_feature_overlap_ratio: float = 0.01):
        self.max_id_overlap = max_id_overlap
        self.max_feature_overlap_ratio = max_feature_overlap_ratio

    def analyze(self, train: Sequence[Example], eval_set: Sequence[Example]) -> ContaminationReport:
        train_ids = {e.example_id for e in train}
        eval_ids = {e.example_id for e in eval_set}
        train_f = {e.feature_hash for e in train}
        eval_f = {e.feature_hash for e in eval_set}
        id_ov = len(train_ids & eval_ids)
        feat_ov = len(train_f & eval_f)
        ratio = feat_ov / max(len(eval_f), 1)
        contaminated = id_ov > self.max_id_overlap or ratio > self.max_feature_overlap_ratio
        body = {
            "id_ov": id_ov,
            "feat_ov": feat_ov,
            "train_n": len(train),
            "eval_n": len(eval_set),
            "contaminated": contaminated,
        }
        return ContaminationReport(id_ov, feat_ov, len(train), len(eval_set), contaminated, digest(body))
