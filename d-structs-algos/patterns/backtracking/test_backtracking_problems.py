from backtracking_problems import combination_sum, permutations, subsets, word_search


def norm(x):
    """Normalize a list-of-lists so comparison ignores the order results were
    discovered in (backtracking order is an implementation detail)."""
    if isinstance(x, list) and x and isinstance(x[0], list):
        return sorted(sorted(inner) for inner in x)
    return x


cases = [
    (subsets, ([1, 2, 3],), [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]),
    (subsets, ([],), [[]]),
    (subsets, ([7],), [[], [7]]),
    (permutations, ([1, 2, 3],),
        [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]),
    (permutations, ([0, 1],), [[0, 1], [1, 0]]),
    (permutations, ([5],), [[5]]),
    (combination_sum, ([2, 3, 6, 7], 7), [[7], [2, 2, 3]]),
    (combination_sum, ([2, 3, 5], 8), [[2, 2, 2, 2], [2, 3, 3], [3, 5]]),
    (combination_sum, ([2], 1), []),
    (word_search, ([["A", "B", "C", "E"],
                    ["S", "F", "C", "S"],
                    ["A", "D", "E", "E"]], "ABCCED"), True),
    (word_search, ([["A", "B", "C", "E"],
                    ["S", "F", "C", "S"],
                    ["A", "D", "E", "E"]], "SEE"), True),
    (word_search, ([["A", "B", "C", "E"],
                    ["S", "F", "C", "S"],
                    ["A", "D", "E", "E"]], "ABCB"), False),  # can't reuse the B
]


def test(func, args, expected) -> bool:
    print("---------------------------------")
    print(f"{func.__name__}{args}")
    print(f"Expected: {expected}")
    result = func(*args)
    print(f"Actual:   {result}")
    if norm(result) == norm(expected):
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
