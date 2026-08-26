"""The comprehension control that separates refusal from reading ability.

The question: how much of an apparent cross-modal safety gap is a
reading-ability artifact rather than an alignment gap?

Built and demonstrated on synthetic, harmless material. No attack corpus and no
published safety benchmark: what is under test is the estimator, not any
model's safety.
"""

__version__ = "0.1.0"

from .instrument import (
    CONDITIONS,
    MIXED_CONDITIONS,
    Condition,
    Observation,
    apparent_gap,
    artifact_share,
    observe,
    real_gap,
)

__all__ = [
    "CONDITIONS",
    "Condition",
    "MIXED_CONDITIONS",
    "Observation",
    "apparent_gap",
    "artifact_share",
    "observe",
    "real_gap",
]
