# Selection Sort

Selection sort is straightforward: find the smallest element in the unsorted portion of the list, move it to the front, then repeat for the remaining elements. Each pass "selects" the next smallest value and places it where it belongs.

It's intuitive and easy to implement, but unlike bubble sort and insertion sort, it never short-circuits — it always scans the entire remaining unsorted section, even if the list is already sorted. This makes it consistently O(n²). Its one practical advantage is that it makes very few writes (at most n−1 swaps), which matters when writing to memory is significantly more expensive than reading.

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
