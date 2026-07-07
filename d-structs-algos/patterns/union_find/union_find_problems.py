"""Union-Find problems — each a thin layer over the UnionFind engine.

The pattern that connects them: edges arrive and you keep answering
connectivity as they do, without ever re-traversing the graph.
"""

from union_find import UnionFind


def count_components(n: int, edges: list[tuple[int, int]]) -> int:
    """Number of connected components in an undirected graph with nodes 0..n-1.

    Start with n singletons; every edge that merges two distinct sets drops the
    component count by one (UnionFind.count tracks this for us).
    """
    uf = UnionFind(n)
    for a, b in edges:
        uf.union(a, b)
    return uf.count


def has_redundant_connection(edges: list[tuple[int, int]]) -> tuple[int, int] | None:
    """The first edge that creates a cycle in an undirected graph built by
    adding edges in order (nodes are 1-indexed); None if the graph stays a
    forest.

    An edge closes a cycle exactly when its two endpoints are *already* in the
    same set — i.e. when union() reports it merged nothing.
    """
    if not edges:
        return None
    max_node = max(max(a, b) for a, b in edges)
    uf = UnionFind(max_node + 1)      # +1 so a 1-indexed max node fits
    for a, b in edges:
        if not uf.union(a, b):
            return (a, b)
    return None


def num_provinces(is_connected: list[list[int]]) -> int:
    """Count 'provinces' — connected groups of cities — from an adjacency
    matrix where is_connected[i][j] == 1 means cities i and j are directly
    linked. (LeetCode 547.)
    """
    n = len(is_connected)
    uf = UnionFind(n)
    for i in range(n):
        for j in range(i + 1, n):     # matrix is symmetric; upper triangle only
            if is_connected[i][j] == 1:
                uf.union(i, j)
    return uf.count
