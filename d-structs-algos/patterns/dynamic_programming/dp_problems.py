"""Classic dynamic-programming problems, each solved bottom-up.

Every solution follows the same four-step method (see README): define the
state in one sentence, write the recurrence, name the base cases, fill in
dependency order. The docstrings state each step explicitly — that narration
is the interview skill, more than the code.
"""


def climbing_stairs(n: int) -> int:
    """Number of distinct ways to climb n steps taking 1 or 2 at a time.

    State: ways(i) = ways to reach step i.
    Recurrence: ways(i) = ways(i-1) + ways(i-2) — the last move was 1 or 2.
    Base: ways(0) = 1 (stand still), ways(1) = 1.
    Space-shrunk: only the last two values are ever needed.
    """
    if n < 0:
        raise ValueError("n must be >= 0")
    two_back, one_back = 1, 1  # ways(0), ways(1)
    for _ in range(2, n + 1):
        two_back, one_back = one_back, one_back + two_back
    return one_back


def house_robber(values: list[int]) -> int:
    """Max sum of non-adjacent elements (rob houses, never two neighbors).

    State: best(i) = max loot considering the first i houses.
    Recurrence: best(i) = max(best(i-1),            # skip house i
                              best(i-2) + values[i]) # rob it
    Base: best(-1) = 0, best(0) = values[0].
    """
    skip, take = 0, 0  # best(i-2), best(i-1) rolling
    for value in values:
        skip, take = take, max(take, skip + value)
    return take


def coin_change(coins: list[int], amount: int) -> int:
    """Fewest coins summing to amount; -1 if impossible. (Unbounded supply.)

    State: dp[a] = fewest coins to make amount a.
    Recurrence: dp[a] = 1 + min(dp[a - c] for usable c).
    Base: dp[0] = 0.
    The greedy trap: coins (1, 3, 4), amount 6 — greedy takes 4+1+1 (3 coins),
    DP finds 3+3 (2 coins). That counterexample is why this is DP.
    """
    INF = amount + 1  # any real answer uses at most `amount` coins
    dp = [0] + [INF] * amount
    for a in range(1, amount + 1):
        for coin in coins:
            if coin <= a and dp[a - coin] + 1 < dp[a]:
                dp[a] = dp[a - coin] + 1
    return dp[amount] if dp[amount] != INF else -1


def longest_common_subsequence(a: str, b: str) -> int:
    """Length of the longest subsequence (not substring!) common to a and b.

    State: dp[i][j] = LCS length of prefixes a[:i] and b[:j].
    Recurrence: chars match -> dp[i-1][j-1] + 1
                else        -> max(dp[i-1][j], dp[i][j-1])
    Base: dp[0][*] = dp[*][0] = 0 (an empty prefix shares nothing).
    """
    rows, cols = len(a), len(b)
    dp = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[rows][cols]
