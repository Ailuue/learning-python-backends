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

    def adjacent_nodes(self, node: int):
        if node not in self.graph:
            return None
        return self.graph[node]

    def unconnected_vertices(self) -> list[int]:
        unconnected = []
        for key in self.graph:
            if not self.graph[key]:
                unconnected.append(key)
        return unconnected

    def edge_exists(self, u: int, v: int) -> bool:
        if u in self.graph and v in self.graph:
            return (v in self.graph[u]) and (u in self.graph[v])
        return False
    
    def breadth_first_search(self, v):
        if v not in self.graph:
            return []
        visited = []
        explore = [v]
        while explore:
            node = explore.pop(0)
            if node in visited:
                continue
            visited.append(node)
            for neighbor in sorted(self.graph[node]):
                if neighbor not in visited:
                    explore.append(neighbor)
        return visited
    
    def depth_first_search(self, start_vertex):
        visited = []
        self.depth_first_search_r(visited, start_vertex)
        return visited
        
    def depth_first_search_r(self, visited, current_vertex):
        visited.append(current_vertex)
        for neighbor in sorted(self.graph[current_vertex]):
            if neighbor not in visited:
                self.depth_first_search_r(visited, neighbor)