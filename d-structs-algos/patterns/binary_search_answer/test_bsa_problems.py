from bsa_problems import find_min_rotated, min_eating_speed, search_rotated, ship_within_days

cases = [
    (search_rotated, ([4, 5, 6, 7, 0, 1, 2], 0), 4),
    (search_rotated, ([4, 5, 6, 7, 0, 1, 2], 3), -1),
    (search_rotated, ([1], 1), 0),
    (search_rotated, ([5, 1, 3], 5), 0),
    (search_rotated, ([1, 2, 3, 4, 5], 4), 3),        # not actually rotated
    (find_min_rotated, ([3, 4, 5, 1, 2],), 1),
    (find_min_rotated, ([4, 5, 6, 7, 0, 1, 2],), 0),
    (find_min_rotated, ([11, 13, 15, 17],), 11),      # rotation of 0
    (find_min_rotated, ([2, 1],), 1),
    (min_eating_speed, ([3, 6, 7, 11], 8), 4),
    (min_eating_speed, ([30, 11, 23, 4, 20], 5), 30),
    (min_eating_speed, ([30, 11, 23, 4, 20], 6), 23),
    (min_eating_speed, ([1], 1), 1),
    (ship_within_days, ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5), 15),
    (ship_within_days, ([3, 2, 2, 4, 1, 4], 3), 6),
    (ship_within_days, ([1, 2, 3, 1, 1], 4), 3),
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
