from stack import *

run_cases = [
    (["a", "b", "c"], 3),
    (["x"], 1),
]

submit_cases = run_cases + [
    ([], 0),
    (["a", "b", "c", "d", "e"], 5),
]


def test_size(items, expected_size):
    print("---------------------------------")
    s = Stack()
    for item in items:
        s.push(item)
    print(f"Pushed: {items}")
    print(f"Expected size: {expected_size}, Actual: {s.size()}")
    if s.size() == expected_size:
        print("Pass")
        return True
    print("Fail")
    return False


def main():
    passed = 0
    failed = 0
    skipped = len(submit_cases) - len(size_cases)
    for case in size_cases:
        if test_size(*case):
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


if "__RUN__" in globals():
    size_cases = run_cases
else:
    size_cases = submit_cases

main()
