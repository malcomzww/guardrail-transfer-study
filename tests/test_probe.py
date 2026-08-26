"""Probe validity, which is the assumption doing all the work.

`instrument.py` assumes the comprehension probe is perfect. These quantify what
happens when it is not, in both directions, because a reviewer will attack this
assumption first and the right response is a number rather than a defence.
"""

from __future__ import annotations

import pytest

from guardrail_transfer_study.instrument import CONDITIONS, Condition
from guardrail_transfer_study.probe import (
    PROBES,
    Probe,
    estimate_with_probe,
    max_tolerable_false_pass,
)


def _by_name(name: str) -> Probe:
    return next(p for p in PROBES if p.name == name)


def test_a_perfect_probe_recovers_the_true_rate():
    """The assumption instrument.py makes, verified rather than trusted."""
    ideal = _by_name("ideal")
    for condition in CONDITIONS:
        result = estimate_with_probe(condition, ideal)
        assert abs(result.residual_bias) < 1e-12


def test_an_easy_probe_lets_the_bias_back_in():
    """The failure that matters.

    A probe a non-comprehending model can pass admits unparsed inputs to the
    conditioned set, and those decline at 1.0 -- which is precisely the bias the
    control exists to remove.
    """
    for condition in CONDITIONS:
        if condition.legibility >= 0.95:
            continue
        result = estimate_with_probe(condition, _by_name("too-easy"))
        # Threshold set from the least-affected condition rather than guessed:
        # text-secondary at 0.84 legibility leaks 1.6 points, and the worst
        # condition leaks 8.6.
        assert result.residual_bias > 0.015


def test_residual_bias_grows_as_the_probe_gets_easier():
    condition = CONDITIONS[-1]
    biases = [
        estimate_with_probe(condition, _by_name(name)).residual_bias
        for name in ("ideal", "slightly-easy", "too-easy")
    ]
    for earlier, later in zip(biases, biases[1:], strict=False):
        assert later > earlier


def test_a_hard_probe_costs_precision_more_than_accuracy():
    """The opposite failure, and the milder one.

    Discarding parsed inputs at random shrinks the sample without moving the
    estimate much. It is wasteful rather than wrong.
    """
    condition = CONDITIONS[-1]
    hard = estimate_with_probe(condition, _by_name("too-hard"))
    easy = estimate_with_probe(condition, _by_name("too-easy"))
    assert abs(hard.residual_bias) < abs(easy.residual_bias)
    assert hard.admitted_fraction < easy.admitted_fraction


def test_a_correlated_probe_is_worse_than_an_uncorrelated_one():
    """The subtle case.

    A probe that gets harder exactly where reading gets harder discards data
    non-randomly, so its errors stop cancelling -- and the estimator is biased
    again by a mechanism the design was built to remove.
    """
    condition = CONDITIONS[-1]
    plain = estimate_with_probe(condition, _by_name("too-hard"))
    correlated = estimate_with_probe(condition, _by_name("correlated-hard"))
    assert abs(correlated.residual_bias) > abs(plain.residual_bias)
    assert correlated.admitted_fraction < plain.admitted_fraction


def test_a_probe_that_rejects_everything_yields_no_estimate():
    """NaN rather than a number, because there is nothing to divide by.

    Returning zero here would look like a measured refusal rate of zero.
    """
    condition = CONDITIONS[0]
    useless = Probe("useless", false_pass=0.0, false_fail=1.0)
    result = estimate_with_probe(condition, useless)
    assert result.admitted_fraction == 0.0
    assert result.estimated_decline != result.estimated_decline  # NaN


def test_admitted_fraction_stays_a_proportion():
    for condition in CONDITIONS:
        for probe in PROBES:
            result = estimate_with_probe(condition, probe)
            assert 0.0 <= result.admitted_fraction <= 1.0


def test_probe_requirement_is_strictest_where_legibility_is_lowest():
    """The design consequence worth stating.

    Fewer parsed inputs means more unparsed ones available to leak through, so
    the false-pass budget shrinks exactly where the study most needs the control
    to work.
    """
    by_name = {c.name: c for c in CONDITIONS}
    easy = max_tolerable_false_pass(by_name["text-primary"], 0.01)
    hard = max_tolerable_false_pass(by_name["image-low-resource"], 0.01)
    assert hard < easy / 5


def test_a_looser_tolerance_permits_a_worse_probe():
    condition = CONDITIONS[-1]
    assert max_tolerable_false_pass(condition, 0.05) > max_tolerable_false_pass(
        condition, 0.01
    )


def test_a_fully_legible_condition_needs_no_probe():
    """With nothing unparsed, there is nothing for a false pass to admit."""
    clean = Condition("clean", legibility=1.0, true_decline=0.8)
    for probe in PROBES:
        if probe.false_fail >= 1.0:
            continue
        result = estimate_with_probe(clean, probe)
        assert abs(result.residual_bias) < 1e-12


@pytest.mark.parametrize(
    "kwargs",
    [
        {"false_pass": -0.1, "false_fail": 0.0},
        {"false_pass": 1.1, "false_fail": 0.0},
        {"false_pass": 0.0, "false_fail": -0.1},
        {"false_pass": 0.0, "false_fail": 1.1},
    ],
)
def test_invalid_probes_are_rejected(kwargs):
    with pytest.raises(ValueError):
        Probe("bad", **kwargs)


def test_nonpositive_tolerance_is_rejected():
    with pytest.raises(ValueError):
        max_tolerable_false_pass(CONDITIONS[0], 0.0)
