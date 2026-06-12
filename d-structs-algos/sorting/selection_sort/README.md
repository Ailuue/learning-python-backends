# Selection Sort

On each pass, finds the minimum element in the unsorted region and swaps it to the front.

## How it works

```
[5, 3, 1, 4]
         ↑ min in [5,3,1,4] is 1 → swap with index 0 → [1, 3, 5, 4]
           ↑ min in [3,5,4] is 3 → already in place  → [1, 3, 5, 4]
             ↑ min in [5,4] is 4 → swap              → [1, 3, 4, 5]
```

## Complexity

| Case | Time | Space |
|---|---|---|
| All cases | O(n²) | O(1) |

Unlike bubble sort and insertion sort, selection sort has **no best case** — it always scans the full unsorted region to find the minimum, even if the list is already sorted.

**One advantage:** selection sort makes at most **n−1 swaps** (one per pass). This makes it useful in contexts where writes are expensive and comparisons are cheap.

## Running tests

```bash
python test_selection_sort.py
```
