from graph import *

# ── edge_exists ──────────────────────────────────────────────────────────────

edge_run_cases: list[tuple] = [
    (
        [(0, 1), (2, 0)],
        ([(1, 0), (1, 2), (2, 0)], [True, False, True]),
    ),
    (
        [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)],
        ([(0, 1), (1, 2), (0, 4), (2, 5), (5, 0)], [True, True, False, False, False]),
    ),
]
edge_submit_cases: list[tuple] = edge_run_cases + [
    (
        [(0, 1), (2, 4), (2, 1), (3, 1), (4, 5)],
        ([(5, 4), (1, 5), (0, 4), (2, 5), (1, 3)], [True, False, False, False, True]),
    ),
]

# ── BFS ──────────────────────────────────────────────────────────────────────

bfs_run_cases: list[tuple] = [
    ([(0, 1), (0, 2), (1, 3), (1, 4)], 0, [0, 1, 2, 3, 4]),  # tree: level-order
    ([(0, 1), (1, 2), (2, 3), (3, 0)], 0, [0, 1, 3, 2]),      # cycle: both neighbours enqueued before going deep
]
bfs_submit_cases: list[tuple] = bfs_run_cases + [
    ([(0, 1), (1, 2), (2, 3)], 0, [0, 1, 2, 3]),              # linear
    ([(0, 1), (1, 2), (2, 3), (3, 4)], 2, [2, 1, 3, 0, 4]),  # start mid-graph
]

# ── DFS ──────────────────────────────────────────────────────────────────────

dfs_run_cases: list[tuple] = [
    ([(0, 1), (0, 2), (1, 3), (1, 4)], 0, [0, 1, 3, 4, 2]),  # tree: depth before siblings
    ([(0, 1), (1, 2), (2, 3), (3, 0)], 0, [0, 1, 2, 3]),      # cycle: follows path all the way around
]
dfs_submit_cases: list[tuple] = dfs_run_cases + [
    ([(0, 1), (1, 2), (2, 3)], 0, [0, 1, 2, 3]),              # linear
    ([(0, 1), (1, 2), (2, 3), (3, 4)], 2, [2, 1, 0, 3, 4]),  # start mid-graph
]


def test_edge_exists(edges_to_add: list, edges_to_check: tuple) -> bool:
    print("=================================")
    graph = Graph()
    for edge in edges_to_add:
        graph.add_edge(edge[0], edge[1])
        print(f"Added edge: {edge}")
    print("---------------------------------")
    try:
        actual = []
        for i, edge in enumerate(edges_to_check[0]):
            exists = graph.edge_exists(edge[0], edge[1])
            actual.append(exists)
            print(f"{edge} exists:")
            print(f" - Expecting: {edges_to_check[1][i]}")
            print(f" - Actual: {exists}")
        if actual == edges_to_check[1]:
            print("Pass \n")
            return True
        print("Fail \n")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_bfs(edges_to_add: list, start: int, expected: list) -> bool:
    print("=================================")
    graph = Graph()
    for edge in edges_to_add:
        graph.add_edge(edge[0], edge[1])
        print(f"Added edge: {edge}")
    print(f"BFS from {start}")
    print(f" - Expecting: {expected}")
    try:
        actual = graph.breadth_first_search(start)
        print(f" - Actual:    {actual}")
        if actual == expected:
            print("Pass \n")
            return True
        print("Fail \n")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_dfs(edges_to_add: list, start: int, expected: list) -> bool:
    print("=================================")
    graph = Graph()
    for edge in edges_to_add:
        graph.add_edge(edge[0], edge[1])
        print(f"Added edge: {edge}")
    print(f"DFS from {start}")
    print(f" - Expecting: {expected}")
    try:
        actual = graph.depth_first_search(start)
        print(f" - Actual:    {actual}")
        if actual == expected:
            print("Pass \n")
            return True
        print("Fail \n")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main() -> None:
    passed = 0
    failed = 0

    print("──── edge_exists ────────────────")
    for case in edge_cases:
        if test_edge_exists(*case):
            passed += 1
        else:
            failed += 1

    print("──── BFS ────────────────────────")
    for case in bfs_cases:
        if test_bfs(*case):
            passed += 1
        else:
            failed += 1

    print("──── DFS ────────────────────────")
    for case in dfs_cases:
        if test_dfs(*case):
            passed += 1
        else:
            failed += 1

    if failed == 0:
        print("============= PASS ==============")
    else:
        print("============= FAIL ==============")
    print(f"{passed} passed, {failed} failed")


if "__RUN__" in globals():
    edge_cases = edge_run_cases
    bfs_cases = bfs_run_cases
    dfs_cases = dfs_run_cases
else:
    edge_cases = edge_submit_cases
    bfs_cases = bfs_submit_cases
    dfs_cases = dfs_submit_cases

main()
