# Two Pointers Problems

**Two pointers** replaces a nested O(n²) scan with a single pass by walking two
indexes through the data and using a property of the input — usually
**sortedness** — to rule out huge swaths of pairs without checking them.

## The signal

- "Find a pair/triple in a **sorted** array that sums to..." — converging
  pointers from both ends. Sum too small? Only moving `left` up can help. Too
  big? Only moving `right` down can. Every step provably discards a whole row
  of the pair-matrix; that's the O(n) argument.
- "Compare a sequence from **both ends**" (palindromes, container walls).
- "Do it **in place**" (dedupe, partition) — a slow writer pointer and a fast
  reader pointer.

Difference from a sliding window: a window is one contiguous region; two
pointers may straddle the whole array and move independently. If the problem
says *contiguous subarray*, think window; if it says *pair whose combination
satisfies X*, think pointers.

## The problems ([pointer_problems.py](pointer_problems.py))

| Problem | Move rule |
|---|---|
| `pair_sum_sorted` | converge: sum < target → left++, sum > target → right-- |
| `most_water` | converge: always move the **shorter** wall inward |
| `is_palindrome_alnum` | converge, skipping non-alphanumerics |
| `three_sum` | sort, fix one value, converge the other two; skip duplicates |

Complexities: first three O(n) time, O(1) space. `three_sum` is O(n²) — the
pointer pass eliminates the third nested loop, which is exactly its point.
