# Graph — Adjacency List

Once you decide to represent a graph in code, you need to choose how to store it. The **adjacency list** is the most common approach: for each vertex, keep a list (or set) of all the vertices it connects to. If you want to know who vertex A is connected to, you look up A in the dictionary and get its neighbors directly.

This representation is memory-efficient for **sparse graphs** — graphs where most vertices only connect to a small number of others (like a road network, where each city connects to a handful of nearby cities rather than every city in the country).

This implementation also includes BFS and DFS — two fundamental algorithms for exploring a graph.

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
