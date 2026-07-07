from pointer_problems import is_palindrome_alnum, most_water, pair_sum_sorted, three_sum

cases = [
    (pair_sum_sorted, ([2, 7, 11, 15], 9), (0, 1)),
    (pair_sum_sorted, ([1, 3, 4, 6, 10], 10), (2, 3)),
    (pair_sum_sorted, ([1, 2, 3], 100), None),
    (pair_sum_sorted, ([-5, 0, 5], 0), (0, 2)),
    (most_water, ([1, 8, 6, 2, 5, 4, 8, 3, 7],), 49),
    (most_water, ([1, 1],), 1),
    (most_water, ([4, 3, 2, 1, 4],), 16),
    (is_palindrome_alnum, ("A man, a plan, a canal: Panama",), True),
    (is_palindrome_alnum, ("race a car",), False),
    (is_palindrome_alnum, (" ",), True),
    (three_sum, ([-1, 0, 1, 2, -1, -4],), [(-1, -1, 2), (-1, 0, 1)]),
    (three_sum, ([0, 1, 1],), []),
    (three_sum, ([0, 0, 0, 0],), [(0, 0, 0)]),
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
