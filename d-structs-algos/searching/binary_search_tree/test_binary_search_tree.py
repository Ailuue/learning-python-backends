from binary_search_tree import *
from user import *

run_cases = [
    (3),
    (5),
]

submit_cases = run_cases + [
    (10),
]


def test(num_users: int) -> bool:
    users = get_users(num_users)
    bst = binary_search_tree_node()
    for user in users:
        print(f"Inserting {user} into tree...")
        bst.insert(user)

    print("\nTree:")
    print("-------------------------------------")
    print_tree(bst)
    print("-------------------------------------")

    traversal = bst.inorder()
    is_sorted = all(traversal[i] < traversal[i + 1] for i in range(len(traversal) - 1))
    has_all = sorted(traversal) == sorted(users)

    if is_sorted and has_all:
        print("Pass\n")
        return True
    if not is_sorted:
        print("Fail: inorder traversal is not sorted\n")
    if not has_all:
        print("Fail: tree is missing inserted values\n")
    return False


def main()-> None:
    passed = 0
    failed = 0
    skipped = len(submit_cases) - len(test_cases)
    for test_case in test_cases:
        print("=====================================")
        correct = test(test_case)
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


def print_tree(bst_node: binary_search_tree_node):
    lines = []
    format_tree_string(bst_node, lines)
    print("\n".join(lines))


def format_tree_string(bst_node: binary_search_tree_node | None, lines: list, level: int = 0):
    if bst_node is not None:
        format_tree_string(bst_node.right, lines, level + 1)
        lines.append(" " * 4 * level + "> " + str(bst_node.val))
        format_tree_string(bst_node.left, lines, level + 1)


test_cases = submit_cases
if "__RUN__" in globals():
    test_cases = run_cases

main()
