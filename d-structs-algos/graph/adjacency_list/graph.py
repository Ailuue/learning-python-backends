class Graph:
    def __init__(self):
        self.graph = {}

    def add_edge(self, u: int, v: int) -> None:
        if u not in self.graph:
            self.graph[u] = set()
        if v not in self.graph:
            self.graph[v] = set()
        self.graph[u].add(v)
        self.graph[v].add(u)

    # don't touch below this line

    def edge_exists(self, u: int, v: int) -> bool:
        if u in self.graph and v in self.graph:
            return (v in self.graph[u]) and (u in self.graph[v])
        return False