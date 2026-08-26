# The comprehension control

Built and demonstrated on **synthetic, harmless material**. There is no attack corpus here and no published safety benchmark: what is under test is the estimator, not any model's safety.

A cross-modal safety evaluation reports a refusal rate per condition and reads it as alignment strength. But a model that could not parse the input produces the same observation as one that read the request and declined it. Both count as a refusal; both count as a safety pass.

## Case 1: no real alignment gap exists

Every condition below has the **same** true decline rate by construction. Only legibility varies -- a rendered page is harder to parse than plain text, a lower-resource language harder than a high-resource one. So any gap the naive metric reports is entirely an artifact.

| condition | comprehension | naive decline | conditioned | apparent gap | real gap | artifact |
|---|---|---|---|---|---|---|
| `text-primary` | 0.99 | 0.802 | 0.800 | — | — | — |
| `text-secondary` | 0.84 | **0.832** | 0.800 | +3.0 pp | +0.0 pp | **100%** |
| `text-low-resource` | 0.61 | **0.878** | 0.800 | +7.6 pp | +0.0 pp | **100%** |
| `image-primary` | 0.72 | **0.856** | 0.800 | +5.4 pp | +0.0 pp | **100%** |
| `image-low-resource` | 0.38 | **0.924** | 0.800 | +12.2 pp | +0.0 pp | **100%** |

The naive metric reports up to **+12.2 points** of apparent safety difference where there is none. The size of the invented gap tracks legibility exactly: `image-low-resource` has the lowest comprehension rate (0.38) and the largest fabricated gap.

## Case 2: a real alignment gap exists

An instrument that explains every gap away is not measuring anything. Here alignment genuinely varies across conditions, and the estimator recovers it -- while the naive metric **understates** it.

| condition | comprehension | naive decline | conditioned | apparent gap | real gap |
|---|---|---|---|---|---|
| `text-primary` | 0.99 | 0.861 | 0.860 | — | — |
| `text-secondary` | 0.84 | 0.756 | 0.710 | -10.5 pp | **-15.0 pp** |
| `image-primary` | 0.72 | 0.698 | 0.580 | -16.4 pp | **-28.0 pp** |

**The naive metric understates the real gap by 11.6 points** on `image-primary`. Non-comprehension inflates the weaker condition's refusal rate toward the baseline, so the same confound that invents gaps in case 1 hides them here. The bias has no consistent direction, which is why it cannot be corrected with a fudge factor.

## Why this matters for the dissertation

The cross-modal safety literature reports refusal rates falling when a harmful request arrives as an image, or in a lower-resource language. That is usually read as safety training failing to transfer.

Case 1 shows an evaluation producing exactly that result on a model whose alignment does not vary at all. Case 2 shows the same confound concealing a real gap. **Neither the presence nor the absence of an apparent gap licenses a conclusion about alignment** without a paired comprehension measurement.

## Limitations

- **This validates an estimator, not a model.** No model is evaluated here and no safety claim is made about any system.
- **Closed-form, not sampled.** The bias is an analytic property of the design; sampling would add noise that obscures it. A real study needs confidence intervals, and the estimator being unbiased in expectation says nothing about its variance at realistic sample sizes.
- **Legibility is treated as binary per input.** Real comprehension is graded -- a model can parse half a request -- and a partially understood harmful instruction is a case this decomposition does not cover.
- **The comprehension probe is assumed valid.** In a real study the probe is itself an instrument that needs validating, and a probe that is easier than the task under test would overstate comprehension and under-correct the bias.
- **No attack material.** Deliberately. The dissertation work uses published-benchmark prompts under a release policy requiring supervisor sign-off and aggregate-only reporting. None of that is in this repository.

## Reproduce

```
uv run python scripts/generate_results.py
```

Closed-form arithmetic; identical output on any machine.
