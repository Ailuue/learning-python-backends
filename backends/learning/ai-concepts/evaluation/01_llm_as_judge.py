"""LLM-as-judge: use a model to grade another model's answer.

Run: `python 01_llm_as_judge.py [anthropic|openai]`

When "correct" is fuzzy, a second model call can grade the first against a rubric.
We give the judge a question, a candidate answer, and explicit criteria, and ask
for a STRUCTURED verdict (pass/fail, 1-5 score, one-line reason) using the
schema-enforced parsing from ../structured-outputs/. A structured verdict is what
makes the judge usable in an automated harness — you can branch and aggregate on
it.

We grade two candidates: one good, one that's confidently wrong, so you can see the
judge separate them. (Judges aren't perfect — they're a scalable approximation of
human review, not ground truth.)
"""
import os
import sys

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


class Verdict(BaseModel):
    passed: bool
    score: int = Field(ge=1, le=5, description="1=terrible, 5=excellent")
    reason: str


QUESTION = "What does the SQL keyword JOIN do?"
CANDIDATES = {
    "good": "JOIN combines rows from two or more tables based on a related column between them.",
    "wrong": "JOIN permanently merges two tables into one and deletes the originals.",
}


def judge_prompt(answer: str) -> str:
    return (
        "You are grading an answer for factual correctness and clarity.\n"
        f"Question: {QUESTION}\n"
        f"Answer to grade: {answer}\n\n"
        "Pass only if the answer is factually correct. Give a 1-5 score and a brief reason."
    )


def judge_anthropic(answer: str) -> Verdict:
    import anthropic

    client = anthropic.Anthropic()
    r = client.messages.parse(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
        max_tokens=512,
        messages=[{"role": "user", "content": judge_prompt(answer)}],
        output_format=Verdict,
    )
    # parsed_output is None when the model's reply does not validate against
    # the schema — a real outcome worth surfacing, not an impossible one.
    if r.parsed_output is None:
        raise ValueError("judge output did not match the Verdict schema")
    return r.parsed_output


def judge_openai(answer: str) -> Verdict:
    from openai import OpenAI

    client = OpenAI()
    r = client.beta.chat.completions.parse(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=512,
        messages=[{"role": "user", "content": judge_prompt(answer)}],
        response_format=Verdict,
    )
    parsed = r.choices[0].message.parsed
    if parsed is None:
        raise ValueError("judge output did not match the Verdict schema")
    return parsed


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    judges = {"anthropic": judge_anthropic, "openai": judge_openai}
    for provider, judge in judges.items():
        if which not in (provider, "both"):
            continue
        print(f"\n=== judge: {provider} ===")
        try:
            for label, answer in CANDIDATES.items():
                v = judge(answer)
                mark = "PASS" if v.passed else "FAIL"
                print(f"  [{label:>5}] {mark} score={v.score} — {v.reason}")
        except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
            print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
