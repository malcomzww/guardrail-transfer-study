"""Estimator properties, checked against closed forms.

The claim this repo makes is that a naive refusal rate is a biased estimator and
the conditioned one is not. That is checkable exactly, so these tests derive the
expected values independently rather than asserting the code agrees with itself.

Also asserted: the repository contains no attack material. That is a release
constraint, not a nicety, and a test is the only way it stays true as the code
changes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from guardrail_transfer_study import (
    CONDITIONS,
    MIXED_CONDITIONS,
    Condition,
    apparent_gap,
    artifact_share,
    observe,
    real_gap,
)


def test_conditioned_rate_recovers_the_true_decline_exactly():
    """The estimator is unbiased by construction, and that is the whole point."""
    for condition in CONDITIONS + MIXED_CONDITIONS:
        obs = observe(condition)
        assert abs(obs.conditioned_decline_rate - condition.true_decline) < 1e-12


def test_naive_rate_matches_its_closed_form():
    """Derived here by hand rather than by calling the same code path.

    naive = legibility * true_decline + (1 - legibility) * 1.0
    """
    for condition in CONDITIONS + MIXED_CONDITIONS:
        p = condition.legibility
        expected = p * condition.true_decline + (1.0 - p) * 1.0
        assert abs(observe(condition).naive_decline_rate - expected) < 1e-12


def test_naive_rate_is_biased_upward_whenever_input_can_be_missed():
    """Non-comprehension is counted as principled refusal.

    Any condition with imperfect legibility and a true decline below 1.0 must
    show a naive rate above its true rate.
    """
    for condition in CONDITIONS + MIXED_CONDITIONS:
        if condition.legibility >= 1.0 or condition.true_decline >= 1.0:
            continue
        obs = observe(condition)
        assert obs.naive_decline_rate > obs.conditioned_decline_rate


def test_perfect_legibility_removes_the_bias():
    """With nothing unparsed, the naive metric is correct.

    Which is why the confound is invisible when every condition is easy to read
    -- and appears the moment one is not.
    """
    c = Condition("clean", legibility=1.0, true_decline=0.7)
    obs = observe(c)
    assert abs(obs.naive_decline_rate - obs.conditioned_decline_rate) < 1e-12
    assert abs(obs.artifact) < 1e-12


def test_bias_grows_as_legibility_falls():
    previous = -1.0
    for legibility in (0.95, 0.8, 0.6, 0.4, 0.2):
        obs = observe(Condition("c", legibility=legibility, true_decline=0.8))
        assert obs.artifact > previous
        previous = obs.artifact


def test_no_real_gap_set_reports_zero_real_gap():
    """Every condition shares one true decline rate by construction."""
    base = observe(CONDITIONS[0])
    for condition in CONDITIONS[1:]:
        assert abs(real_gap(base, observe(condition))) < 1e-12


def test_no_real_gap_set_still_shows_an_apparent_gap():
    """The failure mode the dissertation question is about.

    An evaluation reports a cross-condition safety difference on a model whose
    alignment does not vary at all.
    """
    base = observe(CONDITIONS[0])
    for condition in CONDITIONS[1:]:
        assert apparent_gap(base, observe(condition)) > 0.02


def test_artifact_share_is_total_when_no_real_gap_exists():
    base = observe(CONDITIONS[0])
    for condition in CONDITIONS[1:]:
        assert abs(artifact_share(base, observe(condition)) - 1.0) < 1e-9


def test_apparent_gap_tracks_legibility_not_alignment():
    """The least legible condition must show the largest invented gap."""
    base = observe(CONDITIONS[0])
    others = [observe(c) for c in CONDITIONS[1:]]
    least_legible = min(others, key=lambda o: o.comprehension_rate)
    largest_gap = max(others, key=lambda o: apparent_gap(base, o))
    assert least_legible is largest_gap


def test_estimator_recovers_a_real_gap():
    """An instrument that explains every gap away measures nothing."""
    base = observe(MIXED_CONDITIONS[0])
    for condition in MIXED_CONDITIONS[1:]:
        assert abs(real_gap(base, observe(condition))) > 0.10


def test_naive_metric_understates_a_real_gap():
    """The bias has no consistent direction.

    In the no-gap set it invents gaps; here it hides them, because
    non-comprehension pushes the weaker condition's refusal rate up toward the
    baseline. That is why it cannot be corrected with a fudge factor.
    """
    base = observe(MIXED_CONDITIONS[0])
    for condition in MIXED_CONDITIONS[1:]:
        obs = observe(condition)
        assert abs(apparent_gap(base, obs)) < abs(real_gap(base, obs))


def test_artifact_share_handles_no_apparent_gap():
    """A pair with no observed difference has no decomposition to report.

    Returning 0.0 rather than dividing by zero, and the distinction between
    "no decomposition" and "a decomposition that is zero" is why this is
    explicit.
    """
    a = observe(Condition("a", legibility=1.0, true_decline=0.5))
    b = observe(Condition("b", legibility=1.0, true_decline=0.5))
    assert artifact_share(a, b) == 0.0


def test_rates_stay_probabilities():
    for condition in CONDITIONS + MIXED_CONDITIONS:
        obs = observe(condition)
        for value in (
            obs.naive_decline_rate,
            obs.conditioned_decline_rate,
            obs.comprehension_rate,
        ):
            assert 0.0 <= value <= 1.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"legibility": -0.1, "true_decline": 0.5},
        {"legibility": 1.1, "true_decline": 0.5},
        {"legibility": 0.5, "true_decline": -0.1},
        {"legibility": 0.5, "true_decline": 1.1},
    ],
)
def test_invalid_conditions_are_rejected(kwargs):
    with pytest.raises(ValueError):
        Condition("bad", **kwargs)


def test_observe_rejects_a_nonpositive_sample_size():
    with pytest.raises(ValueError):
        observe(CONDITIONS[0], n=0)


def test_repository_contains_no_attack_material():
    """A release constraint, enforced rather than trusted.

    The dissertation work uses published-benchmark prompts under a policy
    requiring supervisor sign-off and aggregate-only reporting. None of that
    belongs in a public repository, and a test is the only thing that keeps it
    out as the code changes.
    """
    root = Path(__file__).resolve().parents[1]
    # Imperative attack text, not vocabulary. An earlier version banned the
    # word "jailbreak" outright and failed on the release policy that uses it --
    # a check that cannot tell discussing a concept from shipping an attack is
    # a check that gets deleted the first time it is inconvenient.
    banned = (
        "ignore previous instructions",
        "ignore all previous instructions",
        "disregard your instructions",
        "disregard all prior",
        "you are now dan",
        "pretend you have no restrictions",
        "step-by-step instructions for making",
    )

    for path in root.rglob("*"):
        if path.is_dir() or ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.suffix not in {".py", ".md", ".toml", ".yml", ".json", ".txt"}:
            continue
        # This test file names the patterns it forbids, so it excludes itself.
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for phrase in banned:
            assert phrase.lower() not in text, f"{path.name} contains {phrase!r}"
