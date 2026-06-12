# Quick Sort

Divide-and-conquer sort: choose a pivot, partition the array so all smaller elements are to the left and all larger to the right, then recursively sort each side.

## How it works

Uses the **Lomuto partition scheme** — the pivot is always the last element:

```
partition([5, 3, 1, 4], pivot=4)

i = -1  (boundary of the "less than pivot" region)
j=0: 5 ≥ 4 — skip
j=1: 3 < 4  — i=0, swap nums[0] and nums[1] → [3, 5, 1, 4]
j=2: 1 < 4  — i=1, swap nums[1] and nums[2] → [3, 1, 5, 4]
end:         — swap pivot (nums[3]) with nums[i+1=2] → [3, 1, 4, 5]
                                                          ↑ pivot in final position
```

After partition, everything left of index 2 is < 4 and everything right is ≥ 4. Recurse on each side.

## Complexity

| Case | Time | Space (stack) |
|---|---|---|
| Best / Average | O(n log n) | O(log n) |
| Worst (sorted input, bad pivot) | O(n²) | O(n) |

The worst case occurs when the pivot is always the minimum or maximum (e.g. already-sorted input with last-element pivot). Randomising the pivot selection prevents this in practice.

## In-place

Quick sort sorts in place — no extra array is allocated. The only additional space is the O(log n) call stack.

## Running tests

```bash
python test_quick_sort.py
```
