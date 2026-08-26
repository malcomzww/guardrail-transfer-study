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
from .power import (
    PowerResult,
    crossover_sample_size,
    detectable_gap,
    interval_width,
    power_at,
    required_prompts_for_width,
    wilson_interval,
)
from .probe import PROBES, Probe, ProbeResult, estimate_with_probe, max_tolerable_false_pass

__all__ = [
    "CONDITIONS",
    "PROBES",
    "PowerResult",
    "Probe",
    "ProbeResult",
    "crossover_sample_size",
    "detectable_gap",
    "estimate_with_probe",
    "interval_width",
    "max_tolerable_false_pass",
    "power_at",
    "required_prompts_for_width",
    "wilson_interval",
    "Condition",
    "MIXED_CONDITIONS",
    "Observation",
    "apparent_gap",
    "artifact_share",
    "observe",
    "real_gap",
]
