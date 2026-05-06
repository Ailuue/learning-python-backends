from node import *

run_cases = [
    ("Anton Chigurh", ["Llewelyn Moss", "Anton Chigurh"]),
    ("Carson Wells", ["Llewelyn Moss", "Anton Chigurh", "Carson Wells"]),
    ("Ed Tom Bell", ["Llewelyn Moss", "Anton Chigurh", "Carson Wells", "Ed Tom Bell"]),
]

submit_cases = run_cases + [
    (
        "Carla Jean Moss",
        [
            "Llewelyn Moss",
            "Anton Chigurh",
            "Carson Wells",
            "Ed Tom Bell",
            "Carla Jean Moss",
        ],
    ),
    (
        "Wendell",
        [
            "Llewelyn Moss",
            "Anton Chigurh",
            "Carson Wells",
            "Ed Tom Bell",
            "Carla Jean Moss",
            "Wendell",
        ],
    ),
]


def test(linked_list, input, expected_state):
    print("---------------------------------")
    print(f"Linked List: {linked_list_to_str(linked_list)}")
    print(f"Set Next: {input}")
    print(f"Expected: {expected_state}")
    node = Node(input)
    last_node = get_last_node(linked_list)
    last_node.set_next(node)
    try:
        result = linked_list_to_list(linked_list)
    except Exception as e:
        result = f"Error: {e}"
    print(f"Actual: {result}")
    if result == expected_state:
        print("Pass")
        return True
    print("Fail")
    return False


def linked_list_to_list(node):
    result = []
    current = node
    while current:
        result.append(current.val)
        current = current.next
    return result


def get_last_node(node):
    current = node
    while hasattr(current, "next") and current.next:
        current = current.next
    return current


def linked_list_to_str(node):
    current = node
    linked_list_str = ""
    while current and hasattr(current, "val"):
        linked_list_str += current.val + " -> "
        current = current.next

    return linked_list_str


def main():
    passed = 0
    failed = 0
    linked_list = Node("Llewelyn Moss")
    skipped = len(submit_cases) - len(test_cases)
    for test_case in test_cases:
        correct = test(linked_list, *test_case)
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
