# Merge Sort

Divide-and-conquer sort: split the array in half, recursively sort each half, then merge the two sorted halves into one.

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
