# Graph — Adjacency List

An undirected graph backed by a `dict` of `set`s, with BFS and DFS traversal.

## How it works

Each vertex maps to a set of its neighbours. Adding an edge updates both directions (undirected):

```python
graph = {
    1: {2, 3},
    2: {1, 4},
    3: {1},
    4: {2},
}
```

## Operations

| Method | Description | Time |
|---|---|---|
| `add_edge(u, v)` | Add an undirected edge between u and v | O(1) |
| `edge_exists(u, v)` | Check if an edge exists | O(1) avg |
| `adjacent_nodes(node)` | Return the set of neighbours | O(1) |
| `unconnected_vertices()` | Vertices with no edges | O(V) |
| `breadth_first_search(start)` | Level-order traversal — visits closest nodes first | O(V + E) |
| `depth_first_search(start)` | Recursive depth-first traversal | O(V + E) |

## BFS vs DFS

**BFS** uses an explicit queue (`explore` list). It visits all neighbours at the current depth before going deeper — useful for finding shortest paths.

**DFS** is recursive. It follows each branch as far as possible before backtracking — useful for detecting cycles or topological sorting.

```
Graph:  1 — 2 — 4
        |
        3

BFS from 1: [1, 2, 3, 4]   (level by level)
DFS from 1: [1, 2, 4, 3]   (deep first, then backtracks)
```

## Files

| File | Contents |
|---|---|
| `graph.py` | `Graph` class |
| `test_graph.py` | Unit tests |

## Running tests

```bash
python test_graph.py
```
