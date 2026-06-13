# Graph — Adjacency Matrix

An **adjacency matrix** is an alternative way to store a graph. You create a grid — rows and columns both represent vertices — and mark a cell `True` wherever an edge exists between the corresponding pair. Want to know if vertex 2 connects to vertex 5? Check `grid[2][5]` directly.

The trade-off is space: the grid always has V × V cells, even if the graph has very few edges. This makes it wasteful for sparse graphs, but ideal for **dense graphs** where most pairs of vertices are connected — the constant-time edge lookup with zero overhead is worth it.

Comparing this implementation to the [adjacency list](../adjacency_list/) side-by-side is a good way to see how the same abstraction can be built on very different underlying structures.

## How it works

`graph[u][v]` is `True` if there is an edge between vertex u and vertex v. The matrix is always symmetric because edges are undirected.

```
Vertices: 0, 1, 2, 3
add_edge(0, 1), add_edge(1, 2)

     0      1      2      3
0 [False, True,  False, False]
1 [True,  False, True,  False]
2 [False, True,  False, False]
3 [False, False, False, False]
```

## Operations

| Method | Description | Time |
|---|---|---|
| `add_edge(u, v)` | Add an undirected edge | O(1) |
| `edge_exists(u, v)` | Check if an edge exists | O(1) |

## Trade-offs vs adjacency list

| | Adjacency list | Adjacency matrix |
|---|---|---|
| Space | O(V + E) | O(V²) |
| Edge lookup | O(1) avg | O(1) |
| Iterate neighbours | O(degree) | O(V) |
| Best for | Sparse graphs | Dense graphs |

The matrix wastes space when the graph is sparse (many vertices, few edges), but gives guaranteed O(1) edge lookup.

## Files

| File | Contents |
|---|---|
| `graph.py` | `Graph` class |
| `test_graph.py` | Unit tests |

## Running tests

```bash
python test_graph.py
```
