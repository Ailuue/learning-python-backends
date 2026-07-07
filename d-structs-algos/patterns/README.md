# Interview Patterns

The rest of this folder builds data structures from scratch. This section is the
other half of interview prep: **recognizing which pattern a problem is asking
for**. Most coding-interview questions are one of a small number of patterns
wearing a costume — the skill is spotting the signal in the problem statement
and reaching for the matching tool.

| You hear... | Reach for | Folder |
|---|---|---|
| "k largest / k most frequent / k closest" | a **heap** (never a full sort) | [heap/](heap/) |
| "longest/shortest **contiguous** substring or subarray that..." | a **sliding window** | [sliding_window/](sliding_window/) |
| "pair/triple in a **sorted** array", "compare from both ends" | **two pointers** | [two_pointers/](two_pointers/) |
| "number of ways to...", "minimum cost to reach...", "longest common..." | **dynamic programming** | [dynamic_programming/](dynamic_programming/) |
| "all subsets / permutations / combinations", "every way to..." | **backtracking** | [backtracking/](backtracking/) |
| a **matrix** + "connected regions / reachable / fewest steps" | **grid BFS/DFS** | [grid/](grid/) |
| a list of **`[start, end]`** pairs + "overlap / merge / schedule" | **intervals** (sort first) | [intervals/](intervals/) |
| "rotated sorted array", "min/max X such that a condition holds" | **binary search on the answer** | [binary_search_answer/](binary_search_answer/) |
| "next/previous greater or smaller element", "largest rectangle" | **monotonic stack** | [monotonic_stack/](monotonic_stack/) |
| "connected components / merge groups / detect a cycle" as edges arrive | **union-find** | [union_find/](union_find/) |
| "prefix / autocomplete / dictionary of words", wildcard search | **trie** | [trie/](trie/) |

Each folder has a README explaining the pattern, one module of classic problems
solved in the pattern's canonical form, and a test file in this repo's usual
script style (`python run_tests.py patterns` runs all eleven, ~140 cases).

## How to actually practice with these

Reading solutions doesn't build the skill (the same lesson as the deep dives'
EXERCISES files: prediction is where the learning happens). The loop that works:

1. Read the folder README — the pattern, not the solutions.
2. For each problem, read only the docstring contract in the module, then
   **write your own implementation** in a scratch file against the same tests.
3. Compare with the reference solution. If yours differs, decide which is
   better and why — sometimes yours is.
4. Come back a week later and re-derive the two you found hardest.
