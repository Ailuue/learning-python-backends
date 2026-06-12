# Bubble Sort

Repeatedly compares adjacent elements and swaps them if they're out of order. The largest unsorted value "bubbles up" to its correct position on each pass.

## How it works

```
Pass 1: [5, 3, 1, 4] → [3, 1, 4, 5]  (5 bubbles to the end)
Pass 2: [3, 1, 4, 5] → [1, 3, 4, 5]  (3 bubbles to position 2)
Pass 3: [1, 3, 4, 5] → [1, 3, 4, 5]  (no swaps — done early)
```

Two optimisations in the implementation:
- **Early exit**: if a full pass makes no swaps, the list is sorted — stop immediately (this gives O(n) best case)
- **Shrinking window**: after each pass, the last element is guaranteed sorted, so `end` decrements and the inner loop gets shorter

## Complexity

| Case | Time | Space |
|---|---|---|
| Best (already sorted) | O(n) | O(1) |
| Average | O(n²) | O(1) |
| Worst (reverse sorted) | O(n²) | O(1) |

## Running tests

```bash
python test_bubble_sort.py
```
