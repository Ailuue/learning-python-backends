from heap_problems import k_closest_points, kth_largest, top_k_frequent

cases = [
    # (function, args, expected)
    (kth_largest, ([3, 2, 1, 5, 6, 4], 2), 5),
    (kth_largest, ([3, 2, 3, 1, 2, 4, 5, 5, 6], 4), 4),
    (kth_largest, ([7], 1), 7),
    (kth_largest, ([2, 2, 2], 3), 2),
    (top_k_frequent, ([1, 1, 1, 2, 2, 3], 2), [1, 2]),
    (top_k_frequent, ([4], 1), [4]),
    (top_k_frequent, ([5, 5, 6, 6, 7], 2), [5, 6]),  # tie on count -> smaller value first
    (top_k_frequent, ([9, 8, 9, 8, 7, 7, 7], 1), [7]),
    (k_closest_points, ([(1, 3), (-2, 2)], 1), [(-2, 2)]),
    (k_closest_points, ([(3, 3), (5, -1), (-2, 4)], 2), [(3, 3), (-2, 4)]),
    (k_closest_points, ([(3, 3), (1, 1), (2, 2)], 2), [(1, 1), (2, 2)]),
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
