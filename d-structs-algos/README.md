# Data Structures & Algorithms

Data structures and algorithms are the building blocks of software. A **data structure** is a way of organizing data in memory so that common operations (insert, delete, search) are fast. An **algorithm** is a step-by-step procedure for solving a problem. Choosing the right data structure or algorithm for a task is often the difference between a program that runs in milliseconds and one that takes hours.

This folder contains Python implementations of the most important data structures and algorithms — starting from simple linear structures (linked lists, stacks, queues) through trees, graphs, and into the theory of computational hardness (P vs NP). Each subfolder has its own README with an introduction to the concept before the implementation details.

## Data Structures

### [Linked List](linked_list/)
Doubly-ended singly linked list with a head and tail pointer.
- `add_to_head`, `add_to_tail`
- `remove_from_head`, `remove_from_tail`

### [Stack](stack/)
Array-backed stack with an additional `search_and_remove` operation.
- `push`, `pop`, `peek`, `size`, `search_and_remove`

### [Queue](queue/)
Array-backed queue used as the backbone of a matchmaking implementation.
- `push`, `pop`, `peek`, `size`

### [HashMap](hashmap/)
Open-addressing hash map with linear probing. Automatically resizes (doubles) when load factor reaches 70%.
- `insert`, `get`, `resize`, `current_load`

### [Prefix Tree (Trie)](prefix_tree/)
Character-level trie with prefix search and document scanning.
- `insert`, `exists`, `words_with_prefix`
- `find_matches` — scans a document for any word in the trie
- `advanced_find_matches` — same, but accepts a `variations` dict mapping substitute characters to their canonical forms (e.g. `{'@': 'a', '3': 'e'}` matches `d@ng`, `h3ck`)
- `longest_common_prefix`

### [Graph — Adjacency List](graph/adjacency_list/)
Undirected graph backed by a dict of sets.
- `add_edge`, `edge_exists`, `adjacent_nodes`, `unconnected_vertices`
- `breadth_first_search` — level-order traversal using a queue
- `depth_first_search` — recursive depth-first traversal

### [Graph — Adjacency Matrix](graph/matrix/)
Undirected graph backed by a 2-D boolean matrix.
- `add_edge`, `edge_exists`

## Trees

### [Binary Search Tree](searching/binary_search_tree/)
Recursive BST with full traversal and mutation support.
- `insert`, `delete`, `exists`, `height`
- `inorder`, `preorder`, `postorder`

### [Red-Black Tree](red_black_tree/)
Self-balancing BST that maintains red-black invariants on every insert via rotations and recoloring.
- `insert`

## Searching

### [Binary Search](searching/binary_search/)
Iterative binary search on a sorted array.
- `binary_search(target, arr) -> bool`

## Sorting

| Algorithm | File | Complexity |
|---|---|---|
| Bubble Sort | [sorting/bubble_sort/](sorting/bubble_sort/) | O(n²) |
| Selection Sort | [sorting/selection_sort/](sorting/selection_sort/) | O(n²) |
| Insertion Sort | [sorting/insertion_sort/](sorting/insertion_sort/) | O(n²) |
| Merge Sort | [sorting/merge_sort/](sorting/merge_sort/) | O(n log n) |
| Quick Sort | [sorting/quick_sort/](sorting/quick_sort/) | O(n log n) avg |

## P vs NP

### [Traveling Salesman](p-v-np/traveling_salesman/)
Brute-force solution using Heap's algorithm to generate all permutations. Checks whether any Hamiltonian path through the cities has total distance ≤ a given bound.
- `tsp(cities, paths, dist) -> bool`

### [Subset Sum](p-v-np/subset_sum/)
Recursive backtracking solution. Checks whether any subset of the input sums to a target value.
- `subset_sum(nums, target) -> bool`

## Running Tests

Each folder contains a `test_*.py` file. Run any test directly:

```bash
python test_<name>.py
```
