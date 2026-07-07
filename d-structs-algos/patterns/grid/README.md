# Grid BFS / DFS Problems

A 2-D grid is a graph in disguise: each cell is a node, and edges connect it to
its up/down/left/right neighbors (sometimes diagonals too). Once you see that,
"grid" problems are just the BFS and DFS you already know from
[../../graph/](../../graph/) and [../../searching/](../../searching/) — the only
new muscle is generating neighbors with coordinate math and staying inside the
bounds.

## The signal

The input is a matrix and the question is about **connected regions, reachability,
or shortest steps**: "count the islands," "fill this region," "how many minutes
until every orange rots." Two sub-signals pick the traversal:

- **"Is it reachable / how many regions / flood this blob"** → either works;
  DFS is a tidy recursion, BFS an explicit queue. Order within a region doesn't
  matter.
- **"Fewest steps / shortest time / spread level by level"** → **must be BFS**.
  BFS visits cells in increasing distance from the source, so the first time it
  reaches a target, that's the shortest path. DFS gives *a* path, not the
  shortest.

The one bug that sinks these in interviews: **forgetting to mark visited**, or
marking it too late. Mark a cell the instant you enqueue/enter it, not when you
dequeue it — otherwise the same cell rides the queue multiple times and BFS
degrades or loops.

## The problems ([grid_problems.py](grid_problems.py))

| Problem | Traversal | Why |
|---|---|---|
| `num_islands` | DFS | count connected regions of land; order irrelevant |
| `flood_fill` | DFS | recolor one connected region from a seed |
| `rotting_oranges` | **multi-source BFS** | shortest time = BFS layers from *all* rotten cells at once |
| `shortest_path_binary` | BFS | fewest steps corner-to-corner (8-directional) |

The `rotting_oranges` twist worth internalizing: seed the BFS queue with *every*
rotten cell before starting, so all sources expand in lockstep — the layer count
is the answer.
