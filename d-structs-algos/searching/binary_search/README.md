# Binary Search

Iterative binary search on a sorted array — finds a target in O(log n) time.

## How it works

Maintain two pointers, `low` and `high`, that bound the search region. At each step, check the midpoint:
- If `arr[mid] == target` → found
- If `arr[mid] < target` → target is in the right half; move `low` up
- If `arr[mid] > target` → target is in the left half; move `high` down

The search region halves each iteration, so even an array of 1 billion elements takes at most 30 comparisons.

```
arr = [1, 3, 5, 7, 9, 11], target = 7

Step 1: low=0, high=5, mid=2 → arr[2]=5 < 7  → low=3
Step 2: low=3, high=5, mid=4 → arr[4]=9 > 7  → high=3
Step 3: low=3, high=3, mid=3 → arr[3]=7 == 7 → True
```

## Complexity

| | Value |
|---|---|
| Time | O(log n) |
| Space | O(1) |
| Requirement | Input array must be sorted |

## Signature

```python
binary_search(target: int, arr: list) -> bool
```

## Files

| File | Contents |
|---|---|
| `binary_search.py` | `binary_search` function |
| `test_binary_search.py` | Unit tests |

## Running tests

```bash
python test_binary_search.py
```
