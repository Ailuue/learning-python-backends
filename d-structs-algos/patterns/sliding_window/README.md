# Sliding Window Problems

A **sliding window** turns "check every subarray" — O(n²) or worse — into a
single O(n) pass, by maintaining a window `[left, right]` over the sequence
and some running state about what's inside it. The window only ever moves
forward: the right edge grows it, the left edge shrinks it, and each element
enters and leaves at most once.

## The signal

The problem asks for the **longest, shortest, or best *contiguous* run** of
something: "longest substring without repeating characters," "max sum of a
subarray of size k," "longest stretch of 1s if you may flip k zeros."
*Contiguous* is the tell — if the answer may skip elements, it's not a window
problem (it's probably DP or two pointers).

Two flavors:

- **Fixed-size window** — the size is given (k). Slide by adding the entering
  element and subtracting the leaving one; never recompute the whole window.
- **Variable-size window** — grow the right edge greedily; when the window
  becomes *invalid* (a repeat, too many flips), advance the left edge just
  until it's valid again. The answer is the best valid window seen.

The invariant to be able to state out loud in an interview: *between
iterations, the window is always valid, and every element is added once and
removed at most once — that's why two nested-looking loops are still O(n).*

## The problems ([window_problems.py](window_problems.py))

| Problem | Flavor | Running state |
|---|---|---|
| `max_sum_window` | fixed | the window's sum |
| `longest_unique_substring` | variable | last-seen index per character |
| `longest_ones_with_flips` | variable | count of zeros inside the window |

Complexities: all O(n) time; space O(1) except the character map's O(alphabet).
