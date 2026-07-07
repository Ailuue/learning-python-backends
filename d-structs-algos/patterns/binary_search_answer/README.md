# Binary Search on the Answer

Plain [binary search](../../searching/binary_search/) finds a value in a sorted
array. This pattern is the mental leap that trips people up: you can binary
search over a **range of possible answers** even when there's no array to look
in — as long as the answers have a **monotonic yes/no property**.

## The signal

Two shapes show up:

1. **Rotated / partially-sorted arrays.** A sorted array was rotated at some
   pivot ("search in rotated sorted array," "find the minimum"). Still O(log n):
   one half of any slice is always sorted, so you can decide which half to keep.

2. **"Minimum/maximum X such that a condition holds."** "Smallest eating speed
   to finish the bananas in H hours," "least capacity to ship in D days,"
   "minimize the largest split sum." There's no array — the search space is the
   *answer itself* (a speed, a capacity), and you binary search it.

The test for shape 2, the one to state out loud: **is the condition monotonic?**
If a speed of 5 works, does every speed > 5 also work? If yes, the space of
answers looks like `False False False True True True` — and binary search finds
the boundary in O(log(range)) checks, each check being an O(n) "does this
candidate work?" feasibility function.

The template you write once and reuse:

```
lo, hi = min_possible_answer, max_possible_answer
while lo < hi:
    mid = (lo + hi) // 2
    if feasible(mid):
        hi = mid          # mid works; maybe something smaller does too
    else:
        lo = mid + 1      # mid too small; the answer is strictly larger
return lo                  # lo == hi == the boundary
```

## The problems ([bsa_problems.py](bsa_problems.py))

| Problem | Search space | `feasible(mid)` |
|---|---|---|
| `search_rotated` | array indices | is target in the sorted half? |
| `find_min_rotated` | array indices | is `mid` left of the pivot? |
| `min_eating_speed` | speeds 1..max(pile) | can you finish within H hours at this speed? |
| `ship_within_days` | capacities max(w)..sum(w) | do the packages fit in D days? |

The last two never touch a sorted array — that's the whole point of the pattern.
