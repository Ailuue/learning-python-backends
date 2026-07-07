# Union-Find (Disjoint Set) Problems

**Union-Find** (a.k.a. Disjoint Set Union) answers one question absurdly fast:
"are these two things in the same group?" — and lets you **merge** two groups in
near-constant time. It maintains a forest where every element points toward a
**representative** (the root of its tree); two elements are connected iff they
share a root.

With the two standard optimizations — **path compression** (flatten the tree on
every `find`) and **union by rank/size** (always hang the smaller tree under the
bigger) — both operations run in effectively O(1) amortized (technically the
inverse-Ackermann function α(n), which is ≤ 4 for any n you'll ever see).

## The signal

The problem is about **connectivity or grouping under incremental merges**:
"how many connected components," "does adding this edge create a cycle,"
"how many friend circles / provinces," "are these accounts the same person."

The tell that picks Union-Find over BFS/DFS: the edges **arrive one at a time**
and you keep answering connectivity as they do (a *dynamic* graph). BFS/DFS is
better when the graph is fixed and you traverse it once; Union-Find shines when
groups keep merging and you never want to re-traverse.

The cycle-detection insight worth stating: in an undirected graph, an edge
`(a, b)` **closes a cycle** iff `a` and `b` are *already* in the same set before
you union them. That's the whole of "redundant connection."

## The structure ([union_find.py](union_find.py))

A small `UnionFind` class with `find`, `union` (returns False if already
joined), `connected`, and a live `count` of components — the reusable engine the
problems below are one-liners on top of.

## The problems ([union_find_problems.py](union_find_problems.py))

| Problem | Union-Find move |
|---|---|
| `count_components` | union every edge; read `.count` |
| `has_redundant_connection` | the first edge whose two ends are already connected |
| `num_provinces` | union from an adjacency matrix; read `.count` |

Complexities: effectively O(E·α(V)) ≈ O(E) to process all edges.
