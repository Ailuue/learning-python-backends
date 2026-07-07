# Dynamic Programming Problems

**Dynamic programming (DP)** solves a problem by defining it in terms of
smaller versions of itself, then computing the small answers once and reusing
them. Where naive recursion re-solves the same subproblem exponentially many
times, DP visits each subproblem once — usually turning O(2ⁿ) into O(n) or
O(n·m).

## The signal

- "**Number of ways** to..." (climb stairs, make change, form a string)
- "**Minimum/maximum cost** to reach..." while choices at each step depend on
  earlier choices
- "**Longest common** / edit distance / subsequence" — *subsequence* (may skip
  elements) is the DP tell, where *substring/subarray* (contiguous) points at
  a sliding window instead
- Greedy feels tempting but a counterexample kills it (coin change is the
  classic: greedy fails on coins {1, 3, 4} for amount 6)

## The method (say these steps in the interview)

1. **State** — what does `dp[i]` mean, in one sentence?
2. **Recurrence** — how does `dp[i]` follow from smaller states?
3. **Base case(s)** — the smallest states you can answer directly.
4. **Order + answer** — fill so dependencies are ready; name which cell is the
   answer. Then, optionally, shrink space (most 1-D DPs only need the last one
   or two values).

## The problems ([dp_problems.py](dp_problems.py))

| Problem | State `dp[i]` means... | Recurrence |
|---|---|---|
| `climbing_stairs` | ways to reach step i | `dp[i-1] + dp[i-2]` |
| `house_robber` | best loot from the first i houses | `max(dp[i-1], dp[i-2] + v[i])` |
| `coin_change` | fewest coins to make amount i | `1 + min(dp[i - c])` over coins |
| `longest_common_subsequence` | LCS length of prefixes a[:i], b[:j] | match → diag+1, else max(up, left) |

Complexities: stairs/robber O(n) time O(1) space; coin change O(amount·coins);
LCS O(n·m) time and space (space can drop to two rows — a good stretch).
