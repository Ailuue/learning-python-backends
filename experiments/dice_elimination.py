"""
Dice elimination game.

Pool: 12×d6  1×d8  1×d10  1×d12
Score starts at 0.

Each round:
  - Roll every die in the pool.
  - Any die that rolls its max is removed (no score change).
  - If no die rolls max, the one closest to its max is removed and
    (max − rolled) is added to the score.
Repeat until the pool is empty.

Lower score is better.
"""

import random
from functools import lru_cache
from math import comb


def play(verbose: bool = False) -> int:
    pool = [6] * 12 + [8, 10, 12]
    score = 0

    if verbose:
        print("Pool: 12×d6  1×d8  1×d10  1×d12")
        print(f"Score: {score}\n")

    round_n = 0
    while pool:
        round_n += 1
        rolls = [(s, random.randint(1, s)) for s in pool]

        if verbose:
            print(f"--- Round {round_n} ({len(pool)} dice) ---")
            for s, n in rolls:
                flag = "  ← max" if n == s else ""
                print(f"  d{s:2}: {n:2}{flag}")

        maxed = [(s, n) for s, n in rolls if n == s]

        if maxed:
            pool = [s for s, n in rolls if n != s]
            if verbose:
                print(f"\n  {len(maxed)} die(s) hit max → removed. Score unchanged: {score}\n")
        else:
            s, n = min(rolls, key=lambda x: x[0] - x[1])
            gap = s - n
            score += gap
            idx = rolls.index((s, n))
            pool = [rolls[i][0] for i in range(len(rolls)) if i != idx]
            if verbose:
                print(f"\n  No max rolled. d{s} rolled {n} (gap {gap}) → removed. Score: {score}\n")

    if verbose:
        print(f"Done. Final score: {score}")
    return score


def simulate(n: int = 100_000) -> None:
    scores = [play() for _ in range(n)]
    avg = sum(scores) / n
    zero_pct = scores.count(0) / n * 100
    print(f"Simulations    : {n:,}")
    print(f"Average score  : {avg:.2f}")
    print(f"Score of 0     : {zero_pct:.4f}%")


@lru_cache(maxsize=None)
def p_perfect(n6: int, n8: int, n10: int, n12: int) -> float:
    """
    Exact probability of a perfect game (score=0) from pool state (n6, n8, n10, n12).

    Each round, every die independently rolls its max with probability 1/sides.
    We sum over all non-empty subsets of dice that roll max — those dice are
    removed and we recurse on the remaining pool. If no die rolls max the round
    is imperfect, so those outcomes are excluded entirely.

    State space: 13 × 2 × 2 × 2 = 104 states, solved bottom-up via memoization.
    """
    if n6 == 0 and n8 == 0 and n10 == 0 and n12 == 0:
        return 1.0

    total = 0.0
    for k6 in range(n6 + 1):
        p6 = comb(n6, k6) * (1/6)**k6 * (5/6)**(n6 - k6)
        for k8 in range(n8 + 1):
            p8 = comb(n8, k8) * (1/8)**k8 * (7/8)**(n8 - k8)
            for k10 in range(n10 + 1):
                p10 = comb(n10, k10) * (1/10)**k10 * (9/10)**(n10 - k10)
                for k12 in range(n12 + 1):
                    if k6 + k8 + k10 + k12 == 0:
                        continue  # no die hit max → imperfect round, skip
                    p12 = comb(n12, k12) * (1/12)**k12 * (11/12)**(n12 - k12)
                    remaining = p_perfect(n6 - k6, n8 - k8, n10 - k10, n12 - k12)
                    total += p6 * p8 * p10 * p12 * remaining
    return total


def calculate_perfect_odds() -> None:
    prob = p_perfect(12, 1, 1, 1)
    print(f"Exact P(score=0) : {prob:.6f} = {prob * 100:.4f}%")


# ---------------------------------------------------------------------------
# Expected score — exact calculation
#
# State: (n6, n8, n10, n12) — same as p_perfect.
#
# Each round is either:
#   Perfect   (≥1 die hits max): those dice removed, 0 added to score.
#   Imperfect (no die hits max): die with smallest gap removed, gap added to score.
#
# For imperfect rounds we need, for each possible gap value m and each die type,
# the probability that die type achieves the overall minimum gap = m.
# Tie-breaking follows pool order: d6 > d8 > d10 > d12.
#
# Given no die rolled max, each die's gap is uniform on {1, …, sides−1}.
# All gaps are independent, so:
#
#   P(min of n6 d6 gaps = m) = ((6−m)/5)^n6 − ((5−m)/5)^n6
#   P(min of n6 d6 gaps > m) = ((5−m)/5)^n6
#   P(single die gap ≥ m)    = (sides − m) / (sides − 1)
#   P(single die gap > m)    = (sides − m − 1) / (sides − 1)
#   P(single die gap = m)    = 1 / (sides − 1)
#
# For d6 removed at gap m: min-d6-gap = m  AND  all others ≥ m (d6 wins ties)
# For d8 removed at gap m: G8 = m  AND  all d6s > m  AND  d10/d12 ≥ m
# For d10 removed at gap m: G10 = m  AND  d6s > m  AND  G8 > m  AND  d12 ≥ m
# For d12 removed at gap m: G12 = m  AND  d6s > m  AND  G8 > m  AND  G10 > m
# ---------------------------------------------------------------------------

def _min6_eq_m(n6: int, m: int) -> float:
    if n6 == 0 or not 1 <= m <= 5:
        return 0.0
    return ((6 - m) / 5) ** n6 - ((5 - m) / 5) ** n6

def _min6_gt_m(n6: int, m: int) -> float:
    if n6 == 0:
        return 1.0   # no d6s → vacuously true
    if m >= 5:
        return 0.0
    return ((5 - m) / 5) ** n6

def _gap_ge_m(sides: int, m: int) -> float:
    max_gap = sides - 1
    return max(0.0, (max_gap - m + 1) / max_gap) if m >= 1 else 1.0

def _gap_gt_m(sides: int, m: int) -> float:
    max_gap = sides - 1
    return max(0.0, (max_gap - m) / max_gap) if m >= 0 else 1.0

def _gap_eq_m(sides: int, m: int) -> float:
    max_gap = sides - 1
    return 1.0 / max_gap if 1 <= m <= max_gap else 0.0


@lru_cache(maxsize=None)
def e_score(n6: int, n8: int, n10: int, n12: int) -> float:
    if n6 == 0 and n8 == 0 and n10 == 0 and n12 == 0:
        return 0.0

    total = 0.0

    # Perfect rounds: at least one die hits max, no score added this round
    for k6 in range(n6 + 1):
        p6 = comb(n6, k6) * (1/6)**k6 * (5/6)**(n6 - k6)
        for k8 in range(n8 + 1):
            p8 = comb(n8, k8) * (1/8)**k8 * (7/8)**(n8 - k8)
            for k10 in range(n10 + 1):
                p10 = comb(n10, k10) * (1/10)**k10 * (9/10)**(n10 - k10)
                for k12 in range(n12 + 1):
                    if k6 + k8 + k10 + k12 == 0:
                        continue
                    p12 = comb(n12, k12) * (1/12)**k12 * (11/12)**(n12 - k12)
                    total += p6 * p8 * p10 * p12 * e_score(n6-k6, n8-k8, n10-k10, n12-k12)

    # Imperfect rounds: no die hits max, gap added, closest-to-max die removed
    pnm = (5/6)**n6 * (7/8)**n8 * (9/10)**n10 * (11/12)**n12

    if n6:
        for m in range(1, 6):   # d6 max gap = 5
            p = (_min6_eq_m(n6, m)
                 * (_gap_ge_m(8,  m) if n8  else 1.0)
                 * (_gap_ge_m(10, m) if n10 else 1.0)
                 * (_gap_ge_m(12, m) if n12 else 1.0))
            total += pnm * p * (m + e_score(n6 - 1, n8, n10, n12))

    if n8:
        for m in range(1, 8):   # d8 max gap = 7
            p = (_min6_gt_m(n6, m)
                 * _gap_eq_m(8, m)
                 * (_gap_ge_m(10, m) if n10 else 1.0)
                 * (_gap_ge_m(12, m) if n12 else 1.0))
            total += pnm * p * (m + e_score(n6, 0, n10, n12))

    if n10:
        for m in range(1, 10):  # d10 max gap = 9
            p = (_min6_gt_m(n6, m)
                 * (_gap_gt_m(8,  m) if n8  else 1.0)
                 * _gap_eq_m(10, m)
                 * (_gap_ge_m(12, m) if n12 else 1.0))
            total += pnm * p * (m + e_score(n6, n8, 0, n12))

    if n12:
        for m in range(1, 12):  # d12 max gap = 11
            p = (_min6_gt_m(n6, m)
                 * (_gap_gt_m(8,  m) if n8  else 1.0)
                 * (_gap_gt_m(10, m) if n10 else 1.0)
                 * _gap_eq_m(12, m))
            total += pnm * p * (m + e_score(n6, n8, n10, 0))

    return total


def calculate_expected_score() -> None:
    score = e_score(12, 1, 1, 1)
    print(f"Exact E[score]   : {score:.4f}")


if __name__ == "__main__":
    simulate()
    print()
    calculate_perfect_odds()
    calculate_expected_score()
