from dp_problems import climbing_stairs, coin_change, house_robber, longest_common_subsequence

cases = [
    (climbing_stairs, (2,), 2),
    (climbing_stairs, (3,), 3),
    (climbing_stairs, (10,), 89),
    (climbing_stairs, (0,), 1),
    (house_robber, ([1, 2, 3, 1],), 4),
    (house_robber, ([2, 7, 9, 3, 1],), 12),
    (house_robber, ([],), 0),
    (house_robber, ([5],), 5),
    (coin_change, ([1, 2, 5], 11), 3),
    (coin_change, ([2], 3), -1),
    (coin_change, ([1, 3, 4], 6), 2),  # the greedy trap: greedy says 3
    (coin_change, ([1], 0), 0),
    (longest_common_subsequence, ("abcde", "ace"), 3),
    (longest_common_subsequence, ("abc", "abc"), 3),
    (longest_common_subsequence, ("abc", "def"), 0),
    (longest_common_subsequence, ("", "abc"), 0),
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
