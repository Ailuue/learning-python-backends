from balanced import is_balanced

run_cases = [
    ("(", False),
    ("()", True),
    ("(())", True),
]

submit_cases = run_cases + [
    ("()()", True),
    ("(()))", False),
    ("((())())", True),
    ("(()(()", False),
    (")(", False),
    (")()(()", False),
    ("())(()", False),
]


def test(input1: str, expected_output: bool) -> bool:
    print("---------------------------------")
    print(f"Input: {input1}")
    print(f"Expected: {expected_output}")
    result = is_balanced(input1)
    print(f"Actual:   {result}")
    if result == expected_output:
        print("Pass")
        return True
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
