from custom_queue import Queue

run_cases = [
    ([], None),
    (["alice"], "alice"),
    (["alice", "bob"], "alice"),
]

submit_cases = run_cases + [
    (["alice", "bob", "carol"], "alice"),
]


def test_peek(pushes, expected):
    print("---------------------------------")
    q = Queue()
    for item in pushes:
        q.push(item)
    print(f"Pushed in order: {pushes}")
    result = q.peek()
    print(f"Expected peek: {expected}, Actual: {result}")
    if result == expected:
        print("Pass")
        return True
    print("Fail")
    return False


def main():
    passed = 0
    failed = 0
    skipped = len(submit_cases) - len(test_cases)
    for case in test_cases:
        if test_peek(*case):
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
