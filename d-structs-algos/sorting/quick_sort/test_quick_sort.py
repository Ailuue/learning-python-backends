from quick_sort import quick_sort
import time

run_cases = [
    ([2, 1, 3], 0, 2, [1, 2, 3]),
    ([9, 6, 2, 1, 8, 7], 0, 5, [1, 2, 6, 7, 8, 9]),
]

submit_cases = run_cases + [
    ([], 0, -1, []),
    ([1], 0, 0, [1]),
    ([1, 2, 3, 4, 5], 0, 4, [1, 2, 3, 4, 5]),
    ([5, 4, 3, 2, 1], 0, 4, [1, 2, 3, 4, 5]),
    ([0, 1, 6, 4, 7, 3, 2, 8, 5, -9], 0, 9, [-9, 0, 1, 2, 3, 4, 5, 6, 7, 8]),
]


def test(input1: list, input2: int, input3: int, expected_output: list) -> bool:
    print("---------------------------------")
    print(f"Inputs:")
    print(f" * nums: {input1}")
    print(f" * low: {input2}")
    print(f" * high: {input3}")
    print(f"Expected: {expected_output}")
    start = time.time()
    result = input1.copy()
    quick_sort(result, input2, input3)
    end = time.time()
    timeout = 1.00
    if (end - start) < timeout:
        print(f"test completed in less than {timeout * 1000} milliseconds!")
        if result == expected_output:
            print(f"Actual: {result}")
            print("Pass")
            return True
        print(f"Actual: {result}")
        print("Fail")
        return False
    else:
        print(f"test took longer than {timeout * 1000} milliseconds!")
        print(f"Actual: {result}")
        print("Fail")
        return False


def main() -> None:
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
