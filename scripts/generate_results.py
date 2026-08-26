"""Generate results/comprehension-control.md.

Every number in the README comes from here, and each claim is asserted before
the file is written.

    uv run python scripts/generate_results.py

Closed-form: the estimator's bias is an analytic property of the design, so
sampling it would add noise that obscures the demonstration.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from guardrail_transfer_study import (  # noqa: E402
    CONDITIONS,
    MIXED_CONDITIONS,
    apparent_gap,
    artifact_share,
    observe,
    real_gap,
)

OUT = Path(__file__).resolve().parents[1] / "results" / "comprehension-control.md"


def main() -> int:
    flat = [observe(c) for c in CONDITIONS]
    mixed = [observe(c) for c in MIXED_CONDITIONS]

    base, others = flat[0], flat[1:]
    mbase, mothers = mixed[0], mixed[1:]

    # --- assertions on the claims the README makes -----------------------
    # In the no-real-gap set every condition shares the same true decline rate,
    # so a correct estimator must report zero real gap and a 100% artifact share
    # everywhere. Anything else means the conditioning is not working.
    for obs in others:
        assert abs(real_gap(base, obs)) < 1e-12, (
            f"{obs.condition}: real gap should be exactly zero by construction"
        )
        assert abs(artifact_share(base, obs) - 1.0) < 1e-9, (
            f"{obs.condition}: artifact share should be 100%"
        )
        # And the naive metric must show a gap that is not there.
        assert apparent_gap(base, obs) > 0.02, (
            f"{obs.condition}: expected the naive metric to invent a gap"
        )

    # The naive gap must track legibility, not alignment: the least legible
    # condition must show the largest invented gap.
    worst = min(others, key=lambda o: o.comprehension_rate)
    assert worst is max(others, key=lambda o: apparent_gap(base, o)), (
        "the largest apparent gap should be the least legible condition"
    )

    # In the mixed set alignment genuinely varies, so the estimator must recover
    # a real gap rather than explaining every gap away. An instrument that only
    # ever reports "artifact" is not measuring anything.
    for obs in mothers:
        assert abs(real_gap(mbase, obs)) > 0.10, (
            f"{obs.condition}: expected a substantial real gap"
        )
        # And the naive metric must UNDERSTATE it, because non-comprehension
        # pushes the weaker condition's refusal rate up toward the baseline.
        assert abs(apparent_gap(mbase, obs)) < abs(real_gap(mbase, obs)), (
            f"{obs.condition}: expected the naive metric to understate the gap"
        )

    lines: list[str] = []
    lines.append("# The comprehension control\n")
    lines.append(
        "Built and demonstrated on **synthetic, harmless material**. There is no "
        "attack corpus here and no published safety benchmark: what is under "
        "test is the estimator, not any model's safety.\n"
    )
    lines.append(
        "A cross-modal safety evaluation reports a refusal rate per condition "
        "and reads it as alignment strength. But a model that could not parse "
        "the input produces the same observation as one that read the request "
        "and declined it. Both count as a refusal; both count as a safety pass.\n"
    )

    lines.append("## Case 1: no real alignment gap exists\n")
    lines.append(
        "Every condition below has the **same** true decline rate by "
        "construction. Only legibility varies -- a rendered page is harder to "
        "parse than plain text, a lower-resource language harder than a "
        "high-resource one. So any gap the naive metric reports is entirely an "
        "artifact.\n"
    )
    lines.append(
        "| condition | comprehension | naive decline | conditioned | "
        "apparent gap | real gap | artifact |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    lines.append(
        f"| `{base.condition}` | {base.comprehension_rate:.2f} | "
        f"{base.naive_decline_rate:.3f} | {base.conditioned_decline_rate:.3f} | "
        "— | — | — |"
    )
    for obs in others:
        lines.append(
            f"| `{obs.condition}` | {obs.comprehension_rate:.2f} | "
            f"**{obs.naive_decline_rate:.3f}** | "
            f"{obs.conditioned_decline_rate:.3f} | "
            f"{apparent_gap(base, obs) * 100:+.1f} pp | "
            f"{real_gap(base, obs) * 100:+.1f} pp | "
            f"**{artifact_share(base, obs) * 100:.0f}%** |"
        )
    lines.append("")

    biggest = max(others, key=lambda o: apparent_gap(base, o))
    lines.append(
        f"The naive metric reports up to **{apparent_gap(base, biggest) * 100:+.1f} "
        f"points** of apparent safety difference where there is none. The size "
        f"of the invented gap tracks legibility exactly: `{biggest.condition}` "
        f"has the lowest comprehension rate "
        f"({biggest.comprehension_rate:.2f}) and the largest fabricated gap.\n"
    )

    lines.append("## Case 2: a real alignment gap exists\n")
    lines.append(
        "An instrument that explains every gap away is not measuring anything. "
        "Here alignment genuinely varies across conditions, and the estimator "
        "recovers it -- while the naive metric **understates** it.\n"
    )
    lines.append(
        "| condition | comprehension | naive decline | conditioned | "
        "apparent gap | real gap |"
    )
    lines.append("|---|---|---|---|---|---|")
    lines.append(
        f"| `{mbase.condition}` | {mbase.comprehension_rate:.2f} | "
        f"{mbase.naive_decline_rate:.3f} | "
        f"{mbase.conditioned_decline_rate:.3f} | — | — |"
    )
    for obs in mothers:
        lines.append(
            f"| `{obs.condition}` | {obs.comprehension_rate:.2f} | "
            f"{obs.naive_decline_rate:.3f} | "
            f"{obs.conditioned_decline_rate:.3f} | "
            f"{apparent_gap(mbase, obs) * 100:+.1f} pp | "
            f"**{real_gap(mbase, obs) * 100:+.1f} pp** |"
        )
    lines.append("")

    worst_mixed = min(mothers, key=lambda o: o.conditioned_decline_rate)
    understatement = abs(real_gap(mbase, worst_mixed)) - abs(
        apparent_gap(mbase, worst_mixed)
    )
    lines.append(
        f"**The naive metric understates the real gap by "
        f"{understatement * 100:.1f} points** on `{worst_mixed.condition}`. "
        "Non-comprehension inflates the weaker condition's refusal rate toward "
        "the baseline, so the same confound that invents gaps in case 1 hides "
        "them here. The bias has no consistent direction, which is why it cannot "
        "be corrected with a fudge factor.\n"
    )

    lines.append("## Why this matters for the dissertation\n")
    lines.append(
        "The cross-modal safety literature reports refusal rates falling when a "
        "harmful request arrives as an image, or in a lower-resource language. "
        "That is usually read as safety training failing to transfer.\n"
    )
    lines.append(
        "Case 1 shows an evaluation producing exactly that result on a model "
        "whose alignment does not vary at all. Case 2 shows the same confound "
        "concealing a real gap. **Neither the presence nor the absence of an "
        "apparent gap licenses a conclusion about alignment** without a paired "
        "comprehension measurement.\n"
    )

    lines.append("## Limitations\n")
    lines.append(
        "- **This validates an estimator, not a model.** No model is evaluated "
        "here and no safety claim is made about any system.\n"
        "- **Closed-form, not sampled.** The bias is an analytic property of the "
        "design; sampling would add noise that obscures it. A real study needs "
        "confidence intervals, and the estimator being unbiased in expectation "
        "says nothing about its variance at realistic sample sizes.\n"
        "- **Legibility is treated as binary per input.** Real comprehension is "
        "graded -- a model can parse half a request -- and a partially "
        "understood harmful instruction is a case this decomposition does not "
        "cover.\n"
        "- **The comprehension probe is assumed valid.** In a real study the "
        "probe is itself an instrument that needs validating, and a probe that "
        "is easier than the task under test would overstate comprehension and "
        "under-correct the bias.\n"
        "- **No attack material.** Deliberately. The dissertation work uses "
        "published-benchmark prompts under a release policy requiring "
        "supervisor sign-off and aggregate-only reporting. None of that is in "
        "this repository.\n"
    )

    lines.append("## Reproduce\n")
    lines.append("```\nuv run python scripts/generate_results.py\n```\n")
    lines.append("Closed-form arithmetic; identical output on any machine.\n")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print(
        f"  case 1: up to {apparent_gap(base, biggest) * 100:+.1f}pp invented, "
        "100% artifact"
    )
    print(
        f"  case 2: naive understates a real gap by "
        f"{understatement * 100:.1f}pp"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
