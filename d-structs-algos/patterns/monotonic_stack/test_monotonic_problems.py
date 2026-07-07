from monotonic_problems import (
    daily_temperatures,
    largest_rectangle,
    next_greater,
    trapping_rain_water,
)

cases = [
    (next_greater, ([2, 1, 2, 4, 3],), [4, 2, 4, -1, -1]),
    (next_greater, ([5, 4, 3, 2, 1],), [-1, -1, -1, -1, -1]),
    (next_greater, ([1, 2, 3],), [2, 3, -1]),
    (next_greater, ([],), []),
    (daily_temperatures, ([73, 74, 75, 71, 69, 72, 76, 73],), [1, 1, 4, 2, 1, 1, 0, 0]),
    (daily_temperatures, ([30, 40, 50, 60],), [1, 1, 1, 0]),
    (daily_temperatures, ([30, 20, 10],), [0, 0, 0]),
    (largest_rectangle, ([2, 1, 5, 6, 2, 3],), 10),
    (largest_rectangle, ([2, 4],), 4),
    (largest_rectangle, ([5],), 5),
    (largest_rectangle, ([3, 3, 3],), 9),
    (trapping_rain_water, ([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],), 6),
    (trapping_rain_water, ([4, 2, 0, 3, 2, 5],), 9),
    (trapping_rain_water, ([1, 2, 3],), 0),                     # monotonic: no basin
    (trapping_rain_water, ([],), 0),
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
