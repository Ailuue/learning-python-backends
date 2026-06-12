# Graph

Two representations of an undirected graph, demonstrating the trade-offs between adjacency list and adjacency matrix storage.

## Implementations

| Folder | Representation | Space | Edge lookup | BFS / DFS |
|---|---|---|---|---|
| [adjacency_list/](adjacency_list/) | `dict` of `set`s | O(V + E) | O(1) avg | Yes |
| [matrix/](matrix/) | 2-D boolean array | O(V²) | O(1) | No |

## When to use each

**Adjacency list** — sparse graphs (few edges relative to vertices). Space-efficient; easy to iterate over a node's neighbours.

**Adjacency matrix** — dense graphs, or when O(1) worst-case edge lookup matters. Wastes space when most entries are `False`.
