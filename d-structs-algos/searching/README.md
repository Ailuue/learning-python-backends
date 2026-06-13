# Searching

Searching — finding a specific value in a collection — is one of the most common operations in programming. The naive approach is to check every element one by one (linear search), but you can do much better with the right structure or assumption. If data is **sorted**, you can use binary search to find any value in O(log n) time. If you need fast search alongside fast insert and delete, a **binary search tree** organizes data so that every comparison rules out half the remaining values.

## Implementations

| Folder | What it is | Time |
|---|---|---|
| [binary_search/](binary_search/) | Iterative binary search on a sorted array | O(log n) |
| [binary_search_tree/](binary_search_tree/) | Recursive BST with full traversal and mutation | O(log n) avg |
