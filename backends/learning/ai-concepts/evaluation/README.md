# Evaluation

## What is this?

LLM output is non-deterministic — the same prompt can give different answers, and
a prompt tweak that fixes one case can quietly break ten others. You can't eyeball
your way to confidence. **Evaluation** is how you measure whether your LLM feature
actually works, and whether a change made it better or worse.

For a backend engineer this is just *testing*, adapted to a fuzzy output. Instead
of `assertEqual`, you need ways to score answers that are "right" without being
byte-identical.

## Two ways to score

**Exact / programmatic checks** — when there's a known correct answer (a label, a
number, a JSON field), compare directly. Cheap, fast, deterministic. Use this
whenever you can. ([02](02_eval_harness.py))

**LLM-as-judge** — when "correct" is fuzzy (is this summary faithful? is this
answer helpful and grounded?), use a *second* model call to grade the first
against a rubric, returning a structured score. More expensive and itself
imperfect, but it scales judgment you'd otherwise do by hand. ([01](01_llm_as_judge.py))

## The key idea: a fixed test set

The thing that makes evaluation useful is a **dataset you run every time** — a set
of inputs with known-good outputs (or a rubric). Change the prompt, re-run the
set, compare the score. That's a regression test for prompts. Without it, "I think
the new prompt is better" is a vibe, not a measurement.

## What the files cover

| File | What it teaches |
|---|---|
| `01_llm_as_judge.py` | Use a model to grade another model's answer against a rubric, returning a structured pass/score + reason |
| `02_eval_harness.py` | Run a fixed test set through the system, score each case programmatically, report an accuracy number you can track across prompt changes |

## Where this connects

- It's the same instinct as [../../testing-concepts/](../../testing-concepts/),
  applied to probabilistic output — a fixed dataset plus a scorer is a test suite.
- The judge in [01](01_llm_as_judge.py) leans on
  [../structured-outputs/](../structured-outputs/) to get a machine-readable
  verdict.

## How to run

```bash
python 01_llm_as_judge.py
python 02_eval_harness.py anthropic
```
