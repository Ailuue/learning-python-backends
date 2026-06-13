# Graph

A graph is a collection of **nodes** (also called vertices) connected by **edges**. Graphs are one of the most versatile data structures because so many real-world problems are naturally modeled as networks: social networks (people as nodes, friendships as edges), maps (cities as nodes, roads as edges), the internet (pages as nodes, hyperlinks as edges), or dependency trees (tasks as nodes, "must run before" as edges).

Unlike arrays, linked lists, or trees, graphs place no restrictions on how nodes connect. A node can connect to any number of others, connections can form cycles, and parts of the graph can be completely disconnected from each other.

This folder contains two different implementations of the same undirected graph, demonstrating the trade-offs between adjacency list and adjacency matrix storage.

## Implementations

| Folder | Representation | Space | Edge lookup | BFS / DFS |
|---|---|---|---|---|
| [adjacency_list/](adjacency_list/) | `dict` of `set`s | O(V + E) | O(1) avg | Yes |
| [matrix/](matrix/) | 2-D boolean array | O(V²) | O(1) | No |

## When to use each

**Adjacency list** — sparse graphs (few edges relative to vertices). Space-efficient; easy to iterate over a node's neighbours.

**Adjacency matrix** — dense graphs, or when O(1) worst-case edge lookup matters. Wastes space when most entries are `False`.
