from sorting import Influencer, vanity_sort

theprimeagen = Influencer(100, 1)
pokimane = Influencer(800, 2)
spambot = Influencer(0, 200)
lane = Influencer(10, 2)
badcop = Influencer(1, 2)

run_cases = [
    ([badcop, lane], [badcop, lane]),
    ([lane, badcop, pokimane], [badcop, lane, pokimane]),
    ([spambot, theprimeagen], [theprimeagen, spambot]),
]

submit_cases = run_cases + [
    ([], []),
    ([lane], [lane]),
    (
        [pokimane, theprimeagen, spambot, badcop, lane],
        [badcop, lane, theprimeagen, pokimane, spambot],
    ),
]


def test(input1: list[Influencer], expected_output: list[Influencer]) -> bool:
    print("---------------------------------")
    print(f"Input:\n * {input1}")
    print(f"Expected: {expected_output}")
    result = vanity_sort(input1)
    print(f"Actual:   {result}")
    if result == expected_output:
        print("Pass")
        return True
    print("Fail")
    return False


def main()-> None:
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
