# Merge Sort

Merge sort is built on a simple observation: it's much easier to **merge** two already-sorted lists into one sorted list than it is to sort a single unsorted list from scratch. So instead of tackling the whole problem at once, merge sort breaks it down: split the input in half, sort each half (recursively applying the same idea), then merge the two sorted halves together.

This is the divide-and-conquer pattern — split a hard problem into easier subproblems, solve those, combine the results. The recursion bottoms out when a subarray has only one element, which is trivially sorted.

Merge sort is one of the most important algorithms to learn because it introduces divide-and-conquer thinking and has a guaranteed O(n log n) time regardless of input order.

## How it works

```
merge_sort([5, 3, 1, 4])
├── merge_sort([5, 3])
│   ├── merge_sort([5]) → [5]
│   ├── merge_sort([3]) → [3]
│   └── merge([5], [3]) → [3, 5]
├── merge_sort([1, 4])
│   ├── merge_sort([1]) → [1]
│   ├── merge_sort([4]) → [4]
│   └── merge([1], [4]) → [1, 4]
└── merge([3, 5], [1, 4]) → [1, 3, 4, 5]
```

**Merge step:** walk two pointers, one through each sorted half. Append whichever value is smaller, then copy any remainder.

## Complexity

| Case | Time | Space |
|---|---|---|
| All cases | O(n log n) | O(n) |

The O(n) extra space comes from building a new `merged` list at each merge step rather than sorting in place.

**When to prefer it:**
- Guaranteed O(n log n) regardless of input order (unlike quick sort's O(n²) worst case)
- Stable — equal elements keep their original relative order
- Good for linked lists (no random access needed)

## Running tests

```bash
python test_merge_sort.py
```
