# Sorting

Sorting — arranging items in order — is one of the most studied problems in computer science. It comes up constantly: search results ranked by relevance, leaderboards ordered by score, database records returned in alphabetical order. Even other algorithms depend on sorted data (like binary search).

There are many ways to sort a list, and no single algorithm is best in all situations. Simple algorithms like bubble sort and insertion sort are easy to understand and fast on small or nearly-sorted inputs. Divide-and-conquer algorithms like merge sort and quick sort scale to large inputs efficiently. Understanding the trade-offs between them is a core part of learning algorithms.

This folder contains six implementations ranging from simple quadratic algorithms to efficient divide-and-conquer, plus Python's built-in `sorted()` with a custom key.

## Implementations

| Folder | Algorithm | Time (avg) | Time (best) | Space | Stable |
|---|---|---|---|---|---|
| [bubble_sort/](bubble_sort/) | Bubble Sort | O(n²) | O(n) | O(1) | Yes |
| [insertion_sort/](insertion_sort/) | Insertion Sort | O(n²) | O(n) | O(1) | Yes |
| [selection_sort/](selection_sort/) | Selection Sort | O(n²) | O(n²) | O(1) | No |
| [merge_sort/](merge_sort/) | Merge Sort | O(n log n) | O(n log n) | O(n) | Yes |
| [quick_sort/](quick_sort/) | Quick Sort | O(n log n) | O(n log n) | O(log n) | No |
| [sorted/](sorted/) | Python `sorted()` with custom key | O(n log n) | O(n) | O(n) | Yes |

## Key distinctions

- **Stable** — equal elements keep their original relative order (matters when sorting by multiple keys)
- **In-place** — sorts without allocating a separate array (merge sort is the exception here)
- **Adaptive** — performs better on nearly-sorted input (bubble sort and insertion sort short-circuit)
