# guardrail-transfer-study

> **Not started.** This repo is scaffolded — CI, test harness and the results
> pipeline are wired, but no code has been written and there are no
> measurements. The page below is the plan, not a report. It will be rewritten
> around the result when there is one.

Do safety guardrails transfer across language and modality, or do cross-modal safety benchmarks mostly measure whether the model can read the image?

**The one question this repo will answer:**

> How much of the apparent cross-modal safety gap is a reading-ability artifact rather than an alignment gap?

> **Scope constraint.** ETHICS GATE. Published-benchmark prompts only, never novel attacks. No working jailbreak strings in git ever. Aggregate rates only, no per-prompt success transcripts. SAFETY.md stating the question is evaluation validity, not attack improvement. SUPERVISOR SIGN-OFF REQUIRED before public. Scope v1 to two languages and one modality pair.

## Planned method

The control arm itself: every prompt in four conditions plus an OCR-only capability probe, yielding the decomposition of the apparent gap.

Constraints this repo inherits from the portfolio:

- **No GPU.** 24-core CPU, 32 GB RAM, `torch.cuda.is_available()` is False.
  Anything specced for an accelerator is re-scoped to a CPU-measurable
  question or shipped with the untested path explicitly labelled.
- **No live model calls in CI.** Recorded fixtures, so the suite is free and
  deterministic.
- **Every committed number is generated** by `scripts/generate_results.py`,
  carrying its date, hardware, model revision, seed, reproduce command and raw
  artifact path. Nothing is typed by hand.
- **Committed results must be machine-independent** — ratios, orderings and
  invariants. Absolute timings go to a gitignored raw file, because CI
  regenerates results and fails on any diff.

## Paper

Working paper 2 / dissertation: safety alignment across language and modality

Publication order is fixed: **repo public → arXiv preprint → workshop submission.** Never inverted.

## Concepts covered

- 3C refusal vs capability confounds; guardrail transfer across language and modality (DO-7)
- 3C jailbreak taxonomies
- 3C red-teaming methodology, attack success rate as a metric
- 3C input and output guardrails, refusal design, escalation
- 2D cross-modal safety, perception confounds, whether benchmarks measure refusal or reading ability
- 3B construct validity

## Status

| | |
|---|---|
| scaffold, CI, test harness | done |
| implementation | **not started** |
| measurements | **none** |

## License

MIT
