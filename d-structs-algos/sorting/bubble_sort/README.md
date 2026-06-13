# Bubble Sort

Bubble sort is the simplest sorting algorithm to understand. The idea: scan through the list from left to right, and whenever two neighboring elements are in the wrong order, swap them. Repeat this process until no swaps are needed.

With each full pass, the largest remaining unsorted element "bubbles up" to its correct position at the end of the list — like a bubble rising to the surface. After enough passes, everything is in order.

Bubble sort is not efficient for large lists, but it's an ideal first algorithm to study because the mechanics are easy to visualize and reason about.

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
