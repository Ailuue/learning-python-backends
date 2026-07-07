from union_find import UnionFind
from union_find_problems import count_components, has_redundant_connection, num_provinces


def class_ops() -> tuple:
    """Exercise the UnionFind engine directly: union returns False on a repeat,
    connected reflects merges, and count tracks live component totals."""
    uf = UnionFind(5)
    first = uf.union(0, 1)          # True: merged
    repeat = uf.union(1, 0)         # False: already joined
    uf.union(2, 3)
    return (first, repeat, uf.connected(0, 1), uf.connected(0, 2), uf.count)


cases = [
    (class_ops, (), (True, False, True, False, 3)),
    (count_components, (5, [(0, 1), (1, 2), (3, 4)]), 2),
    (count_components, (4, []), 4),
    (count_components, (1, []), 1),
    (count_components, (3, [(0, 1), (1, 2), (0, 2)]), 1),  # extra edge, still one
    (has_redundant_connection, ([(1, 2), (1, 3), (2, 3)],), (2, 3)),
    (has_redundant_connection, ([(1, 2), (2, 3), (3, 4)],), None),  # a tree
    (has_redundant_connection, ([(1, 2), (2, 3), (1, 3), (3, 4)],), (1, 3)),
    (num_provinces, ([[1, 1, 0], [1, 1, 0], [0, 0, 1]],), 2),
    (num_provinces, ([[1, 0, 0], [0, 1, 0], [0, 0, 1]],), 3),
    (num_provinces, ([[1, 1, 1], [1, 1, 1], [1, 1, 1]],), 1),
]


def test(func, args, expected) -> bool:
    print("---------------------------------")
    print(f"{func.__name__}{args}")
    print(f"Expected: {expected}")
    result = func(*args)
    print(f"Actual:   {result}")
    if result == expected:
        print("Pass")
        return True
    print("Fail")
    return False


def main() -> None:
    passed = 0
    failed = 0
    for func, args, expected in cases:
        if test(func, args, expected):
            passed += 1
        else:
            failed += 1
    print("=================================")
    print(f"{passed} passed, {failed} failed")


main()
