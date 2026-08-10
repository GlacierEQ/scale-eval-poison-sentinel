# ISSUE CONTRACT

## Pain
Evaluation sets can silently share exact examples or feature signatures with training data, laundering benchmark scores and weakening confidence in measured generalization.

## Success
- Detect exact example-ID overlap.
- Detect exact feature-hash overlap and report its ratio over unique evaluation feature hashes.
- Bind the exact dataset identities and contamination policy thresholds into the report receipt.
- Refuse malformed/duplicate example identities and invalid policy thresholds.
- Fail closed when observed contamination exceeds the explicit policy.

## Boundary
This repository compares supplied feature hashes exactly. It does **not** compute semantic similarity or near-duplicate embeddings itself. Near-duplicate detection is only represented if an upstream feature-hash process deliberately maps near duplicates into the same signature.
