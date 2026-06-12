# Insertion Sort

Builds a sorted prefix one element at a time by inserting each new element into its correct position among the already-sorted elements to its left.

## How it works

Think of sorting a hand of playing cards: you pick up one card at a time and slide it left until it's in the right place.

```
[5, 3, 1, 4]
 ↑ sorted so far: [5]

Pick 3: slide left past 5 → [3, 5, 1, 4]
Pick 1: slide left past 5, 3 → [1, 3, 5, 4]
Pick 4: slide left past 5 → [1, 3, 4, 5]
```

The inner `while` loop shifts elements right one step at a time until the insertion point is found.

## Complexity

| Case | Time | Space |
|---|---|---|
| Best (already sorted) | O(n) | O(1) |
| Average | O(n²) | O(1) |
| Worst (reverse sorted) | O(n²) | O(1) |

**When to prefer it:** insertion sort outperforms merge sort and quick sort on small arrays (< ~10–20 elements) and is the algorithm CPython uses for small partitions inside `timsort`.

## Running tests

```bash
python test_insertion_sort.py
```
