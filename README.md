# guardrail-transfer-study

**A safety evaluation reports up to 12.2 points of apparent cross-condition
difference on a model whose alignment does not vary at all.** Every point of it
is a reading-ability artifact.

This repo answers one question:

> How much of an apparent cross-modal safety gap is a reading-ability artifact
> rather than an alignment gap?

> **No attack material.** Built and demonstrated on synthetic, harmless
> prompts. There is no attack corpus here, no published safety benchmark and no
> jailbreak text — what is under test is the *estimator*, not any model's
> safety. The dissertation work uses published-benchmark prompts under a release
> policy requiring supervisor sign-off and aggregate-only reporting, and none of
> that is in this repository. A test enforces it.

## The confound

A cross-modal safety evaluation reports a refusal rate per condition and reads
it as alignment strength. But two very different models produce an identical
observation:

- a model that **understood** the request and declined it
- a model that **could not parse** the input at all

Both score as a refusal. Both score as a safety pass. So a model that simply
cannot read a language looks exactly as aligned as one that read the request and
refused.

The fix is a paired **comprehension probe**: a benign task in the same condition
that only a model which parsed the input can pass. Conditioning refusals on
demonstrated comprehension splits the observed gap into an alignment component
and a perception artifact.

## Case 1: the metric invents a gap

Every condition below has the **same** true decline rate by construction. Only
legibility varies.

| condition | comprehension | naive decline | conditioned | apparent gap | real gap | artifact |
|---|---|---|---|---|---|---|
| `text-primary` | 0.99 | 0.802 | 0.800 | — | — | — |
| `text-secondary` | 0.84 | 0.832 | 0.800 | +3.0 pp | +0.0 pp | **100%** |
| `text-low-resource` | 0.61 | 0.878 | 0.800 | +7.6 pp | +0.0 pp | **100%** |
| `image-primary` | 0.72 | 0.856 | 0.800 | +5.4 pp | +0.0 pp | **100%** |
| `image-low-resource` | 0.38 | 0.924 | 0.800 | +12.2 pp | +0.0 pp | **100%** |

The size of the invented gap tracks legibility exactly. `image-low-resource` has
the lowest comprehension rate and the largest fabricated gap — which is the same
ordering a real study would report and read as alignment failure.

## Case 2: the metric hides a real gap

An instrument that explains every gap away measures nothing. Here alignment
genuinely varies, and the naive metric **understates** it:

| condition | comprehension | naive decline | conditioned | apparent gap | real gap |
|---|---|---|---|---|---|
| `text-primary` | 0.99 | 0.861 | 0.860 | — | — |
| `text-secondary` | 0.84 | 0.756 | 0.710 | −10.5 pp | **−15.0 pp** |
| `image-primary` | 0.72 | 0.698 | 0.580 | −16.4 pp | **−28.0 pp** |

**The naive metric understates the real gap by 11.6 points** on
`image-primary`. Non-comprehension inflates the weaker condition's refusal rate
toward the baseline, so the same confound that invents gaps in case 1 conceals
them here.

**The bias has no consistent direction**, which is why it cannot be corrected
with a fudge factor — only with a measurement.

## Why this matters

The cross-modal safety literature reports refusal rates falling when a harmful
request arrives as an image, or in a lower-resource language, and reads that as
safety training failing to transfer.

Case 1 shows an evaluation producing exactly that result on a model whose
alignment does not vary at all. Case 2 shows the same confound concealing a real
gap. **Neither the presence nor the absence of an apparent gap licenses a
conclusion about alignment** without a paired comprehension measurement.

Full tables: [`results/comprehension-control.md`](results/comprehension-control.md).

## Limitations

- **This validates an estimator, not a model.** No model is evaluated here and
  no safety claim is made about any system.
- **Closed-form, not sampled.** The bias is an analytic property of the design,
  so sampling would add noise that obscures it. A real study needs confidence
  intervals, and being unbiased in expectation says nothing about variance at
  realistic sample sizes.
- **Legibility is binary per input.** Real comprehension is graded — a model can
  parse half a request — and a partially understood harmful instruction is a
  case this decomposition does not cover.
- **The comprehension probe is assumed valid.** In a real study the probe is
  itself an instrument needing validation: one easier than the task under test
  would overstate comprehension and under-correct the bias.

## Reproduce

```bash
uv sync --extra dev
uv run python scripts/generate_results.py
uv run pytest
```

Closed-form arithmetic — identical output on any machine. CI regenerates the
results and fails on any diff.

## License

MIT
