# Graph — Adjacency Matrix

An undirected graph backed by a 2-D boolean matrix.

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
