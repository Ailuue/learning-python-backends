from grid_problems import flood_fill, num_islands, rotting_oranges, shortest_path_binary

# Each case uses fresh list literals — these functions mutate the grid in place.
cases = [
    (num_islands, ([["1", "1", "0", "0"],
                    ["1", "0", "0", "1"],
                    ["0", "0", "1", "1"]],), 2),
    (num_islands, ([["1", "1", "1"],
                    ["1", "1", "1"]],), 1),
    (num_islands, ([["0", "0"], ["0", "0"]],), 0),
    (num_islands, ([["1", "0", "1", "0", "1"]],), 3),
    (flood_fill, ([[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2),
        [[2, 2, 2], [2, 2, 0], [2, 0, 1]]),
    (flood_fill, ([[0, 0, 0], [0, 0, 0]], 0, 0, 5),
        [[5, 5, 5], [5, 5, 5]]),
    (flood_fill, ([[1, 0], [0, 1]], 0, 0, 1), [[1, 0], [0, 1]]),  # no-op guard
    (rotting_oranges, ([[2, 1, 1], [1, 1, 0], [0, 1, 1]],), 4),
    (rotting_oranges, ([[2, 1, 1], [0, 1, 1], [1, 0, 1]],), -1),  # bottom-left stranded
    (rotting_oranges, ([[0, 2]],), 0),                            # nothing fresh
    (shortest_path_binary, ([[0, 1], [1, 0]],), 2),
    (shortest_path_binary, ([[0, 0, 0], [1, 1, 0], [1, 1, 0]],), 4),
    (shortest_path_binary, ([[1, 0], [0, 0]],), -1),              # start blocked
    (shortest_path_binary, ([[0]],), 1),
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
