from linked_list import *

run_cases = [
    (["A", "B", "C"], "head", "A", ["B", "C"], "B", "C"),
    (["A", "B", "C"], "tail", "C", ["A", "B"], "A", "B"),
]

submit_cases = run_cases + [
    (["X"], "head", "X", [], None, None),
    (["X"], "tail", "X", [], None, None),
]


def build_list(vals):
    ll = LinkedList()
    for v in vals:
        ll.add_to_tail(Node(v))
    return ll


def list_to_vals(ll):
    return [node.val for node in ll]


def test(vals, end, expected_removed, expected_remaining, expected_head, expected_tail):
    print("---------------------------------")
    ll = build_list(vals)
    print(f"List: {ll}")
    print(f"Removing from {end}")

    if end == "head":
        removed = ll.remove_from_head()
    else:
        removed = ll.remove_from_tail()

    removed_val = removed.val if removed is not None else None
    remaining = list_to_vals(ll)
    head_val = ll.head.val if ll.head is not None else None
    tail_val = ll.tail.val if ll.tail is not None else None

    print(f"Expected removed: {expected_removed}, Actual: {removed_val}")
    print(f"Expected remaining: {expected_remaining}, Actual: {remaining}")
    print(f"Expected head: {expected_head}, Actual: {head_val}")
    print(f"Expected tail: {expected_tail}, Actual: {tail_val}")

    if (
        removed_val == expected_removed
        and remaining == expected_remaining
        and head_val == expected_head
        and tail_val == expected_tail
    ):
        print("Pass")
        return True
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
