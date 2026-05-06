import random
import time
from linked_list import *

run_cases = [
    (10, "Patrick Bateman", "Paul Allen"),
    (100, "Paul Allen", "Paul Allen"),
    (1000, "Paul Allen", "Paul Allen"),
    (10000, "Patrick Bateman", "Paul Allen"),
]

submit_cases = run_cases + [
    (12000, "Paul Allen", "Paul Allen"),
]


def test(num_items: int, first_item: str, last_item: str):
    print("---------------------------------")
    print(f"Adding {num_items} job candidates to a linked list's head")
    linked_list = LinkedList()
    timeout = 1.5
    start = time.time()
    for item in get_items(num_items):
        linked_list.add_to_head(Node(item))

    print(f"Adding {num_items} job candidates to a linked list's tail")
    linked_list2 = LinkedList()
    for item in get_items(num_items):
        linked_list2.add_to_tail(Node(item))
    end = time.time()

    print(f"Expecting to complete in less than {timeout * 1000} milliseconds")
    if (end - start) < timeout:
        print(f"Test completed in less than {timeout * 1000} milliseconds!")
    else:
        print("Fail")
        print(f"Test took too long ({(end - start) * 1000} milliseconds). Speed it up!")
        cleanup_list(linked_list)
        cleanup_list(linked_list2)
        return False

    print("\nChecking the first linked list")
    if not check_links(linked_list, first_item, last_item, num_items):
        cleanup_list(linked_list)
        cleanup_list(linked_list2)
        return False
    print("\nChecking the second linked list")
    if not check_links(linked_list2, last_item, first_item, num_items):
        cleanup_list(linked_list)
        cleanup_list(linked_list2)
        return False

    print("\nPass")
    cleanup_list(linked_list)
    cleanup_list(linked_list2)
    return True


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


def get_items(num):
    random.seed(1)
    options = ["Patrick Bateman", "Paul Allen", "Evelyn Williams", "Luis Carruthers"]
    items = []
    for _ in range(num):
        optionI = random.randint(0, len(options) - 1)
        items.append(options[optionI])
    return items


def check_links(llist, head, tail, expected_length):
    print(f"Expected Head: {head}")
    print(f"Actual Head: {llist.head}")
    if head != llist.head.val:
        print("Fail")
        print("The linked list's head node does not have the expected value")
        print("Check if nodes added to the head are set as the new head node")
        return False
    print(f"Expected Tail: {tail}")
    print(f"Actual Tail: {llist.tail}")
    if tail != llist.tail.val:
        print("Fail")
        print("The linked list's tail node does not have the expected value")
        print("Check if nodes added to the tail are set as the new tail node")
        return False

    actual_length = 0
    for _ in llist:
        actual_length += 1
    print(f"Expected Length: {expected_length}")
    print(f"Actual Length: {actual_length}")
    if expected_length != actual_length:
        print("Fail")
        print("The linked list is not the expected length of linked nodes")
        print("Check if added nodes are set as the new head or tail")
        return False
    return True


def cleanup_list(llist):
    current = llist.head
    while current is not None:
        next_node = current.next
        current.next = None
        current = next_node
    llist.head = None
    llist.tail = None


test_cases = submit_cases
if "__RUN__" in globals():
    test_cases = run_cases

main()
