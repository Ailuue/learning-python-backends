from subset_sum import *

run_cases = [
    ([3, 34, 4, 12, 5, 2], 9, True),
    ([1, 2, 3], 7, False),
]

submit_cases = run_cases + [
    ([1, 2, 3, 8, 9, 10], 7, False),
    ([1, 2, 3, 4, 5, 6, 7, 8, 9], 15, True),
    ([3, 2, 7, 1], 6, True),
    ([10, 20, 30, 40, 50], 60, True),
    (
        [1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
        500,
        False,
    ),
]


def test(nums, target, expected_output):
    print("---------------------------------")
    print(f"Nums: {nums}")
    print(f"Target: {target}")
    print(f"Expected Output: {expected_output}")
    result = subset_sum(nums, target)
    print(f"Actual Output: {result}")
    if result == expected_output:
        print("Pass")
        return True
    else:
        print("Fail")
        return False


def main():
    passed = 0
    failed = 0
    skipped = len(submit_cases) - len(test_cases)
    for test_case in test_cases:
        correct = test(*test_case)
        if correct:
            passed += 1
        else:
            failed += 1
    if failed == 0:
        print("============= PASS ==============")
    else:
        print("============= FAIL ==============")
    if skipped > 0:
        print(f"{passed} passed, {failed} failed, {skipped} skipped")
    else:
        print(f"{passed} passed, {failed} failed")


test_cases = submit_cases
if "__RUN__" in globals():
    test_cases = run_cases

main()
