# Subset Sum

Subset sum is a classic NP-complete problem that is easy to state but hard to solve in general.

The question: given a list of numbers, can you pick some of them (any combination) that add up to exactly a target value? You might think "just try all combinations" — and that's exactly what we do here. The problem is that the number of combinations explodes exponentially as the list grows, making brute force impractical for large inputs.

**Given a list of non-negative integers and a target, does any subset of the list sum exactly to the target?**

```python
subset_sum([3, 1, 4, 9], target=8)   # True  — {4, 3, 1}
subset_sum([3, 1, 4, 9], target=6)   # False — no subset sums to 6
```

## Why it's hard

There are 2ⁿ possible subsets. For 50 numbers that's over a quadrillion combinations — exhaustive search is not practical for large inputs.

## Implementation — recursive backtracking

For each element, make a binary choice: include it or skip it. Recurse on the remaining elements with the updated target.

```
find_subset_sum([3, 1, 4], target=4, index=0)
├── include 3 → find_subset_sum([3, 1, 4], target=1, index=1)
│   ├── include 1 → target=0 → True ✓
│   └── ...
└── skip 3 → find_subset_sum([3, 1, 4], target=4, index=1)
    └── ...
```

**Early pruning:** if `nums[index] > target`, skip it immediately (can't overshoot with non-negatives).

## The P vs NP illustration

- **Finding** a valid subset: O(2ⁿ) — try all combinations
- **Verifying** a claimed subset: O(n) — just sum the elements

## Complexity

| | Time | Space |
|---|---|---|
| Solver | O(2ⁿ) | O(n) call stack |

## Files

| File | Contents |
|---|---|
| `subset_sum.py` | `subset_sum` and `find_subset_sum` |
| `test_subset_sum.py` | Unit tests |

## Running tests

```bash
python test_subset_sum.py
```
