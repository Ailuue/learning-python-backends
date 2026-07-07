from window_problems import longest_ones_with_flips, longest_unique_substring, max_sum_window

cases = [
    (max_sum_window, ([2, 1, 5, 1, 3, 2], 3), 9),
    (max_sum_window, ([1, 2, 3], 3), 6),
    (max_sum_window, ([4, -1, 2, -7, 5, 5], 2), 10),
    (longest_unique_substring, ("abcabcbb",), 3),
    (longest_unique_substring, ("bbbbb",), 1),
    (longest_unique_substring, ("pwwkew",), 3),
    (longest_unique_substring, ("",), 0),
    (longest_unique_substring, ("abba",), 2),  # the left-jump edge case
    (longest_ones_with_flips, ([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2), 6),
    (longest_ones_with_flips, ([0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3), 10),
    (longest_ones_with_flips, ([0, 0, 0], 0), 0),
    (longest_ones_with_flips, ([1, 1], 0), 2),
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
