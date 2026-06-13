# Quick Sort

Quick sort is one of the most widely used sorting algorithms in practice — it's the default sort in many standard libraries, including C's `qsort`. Like merge sort, it uses divide-and-conquer, but it divides differently.

Instead of splitting evenly down the middle, quick sort picks a **pivot** element and rearranges the array so that everything smaller than the pivot ends up on its left, and everything larger on its right. At that point the pivot is in its final sorted position — permanently. Then quick sort repeats on the left and right sections independently.

The key insight is that after partitioning, you never need to compare anything in the left section against anything in the right section again. Each partition step places one element exactly and shrinks the remaining work.

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
