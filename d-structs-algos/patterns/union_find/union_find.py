"""The reusable Union-Find (Disjoint Set Union) engine.

Two optimizations make find/union effectively O(1) amortized:
  - path compression: every find re-points nodes straight at the root
  - union by rank: the shorter tree hangs under the taller, keeping trees flat
"""


class UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))   # each element starts as its own root
        self.rank = [0] * n            # upper bound on each tree's height
        self.count = n                 # number of disjoint sets, kept live

    def find(self, x: int) -> int:
        """Return x's representative, compressing the path on the way up."""
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:  # second pass: point everything at root
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        """Merge the sets of a and b. Return False if they were already joined
        (useful for cycle detection), True if this call actually merged two."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra            # ensure ra is the taller tree
        self.parent[rb] = ra           # hang the shorter under the taller
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        self.count -= 1
        return True

    def connected(self, a: int, b: int) -> bool:
        return self.find(a) == self.find(b)
