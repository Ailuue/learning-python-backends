from interval_problems import can_attend_all, insert_interval, merge_intervals, min_meeting_rooms

cases = [
    (merge_intervals, ([[1, 3], [2, 6], [8, 10], [15, 18]],), [[1, 6], [8, 10], [15, 18]]),
    (merge_intervals, ([[1, 4], [4, 5]],), [[1, 5]]),          # touching merges
    (merge_intervals, ([[1, 4], [0, 4]],), [[0, 4]]),          # unsorted input
    (merge_intervals, ([],), []),
    (merge_intervals, ([[1, 4], [2, 3]],), [[1, 4]]),          # fully contained
    (insert_interval, ([[1, 3], [6, 9]], [2, 5]), [[1, 5], [6, 9]]),
    (insert_interval, ([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]),
        [[1, 2], [3, 10], [12, 16]]),
    (insert_interval, ([], [5, 7]), [[5, 7]]),
    (insert_interval, ([[1, 5]], [6, 8]), [[1, 5], [6, 8]]),   # strictly after
    (can_attend_all, ([[0, 30], [5, 10], [15, 20]],), False),
    (can_attend_all, ([[7, 10], [2, 4]],), True),
    (can_attend_all, ([[1, 2], [2, 3]],), True),               # touching is fine
    (min_meeting_rooms, ([[0, 30], [5, 10], [15, 20]],), 2),
    (min_meeting_rooms, ([[7, 10], [2, 4]],), 1),
    (min_meeting_rooms, ([[1, 5], [2, 6], [3, 7]],), 3),       # all overlap
    (min_meeting_rooms, ([[1, 2], [2, 3], [3, 4]],), 1),       # back-to-back
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
