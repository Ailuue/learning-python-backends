from red_black_tree import *
from user import *

run_cases = [
    (4),
    (8),
]

submit_cases = run_cases + [
    (10),
]


def rbt_inorder(node, NIL):
    if node is NIL or node is None:
        return []
    return rbt_inorder(node.left, NIL) + [node.val] + rbt_inorder(node.right, NIL)


def has_double_red(node, NIL):
    if node is NIL or node is None:
        return False
    if node.red:
        left_red = node.left is not None and node.left is not NIL and node.left.red
        right_red = node.right is not None and node.right is not NIL and node.right.red
        if left_red or right_red:
            return True
    return has_double_red(node.left, NIL) or has_double_red(node.right, NIL)


def black_height(node, NIL):
    if node is NIL or node is None:
        return 0
    left_bh = black_height(node.left, NIL)
    right_bh = black_height(node.right, NIL)
    if left_bh == -1 or right_bh == -1 or left_bh != right_bh:
        return -1
    return left_bh + (0 if node.red else 1)


def test(num_users):
    users = get_users(num_users)
    tree = RBTree()
    for user in users:
        print(f"Inserting {user} into tree...")
        tree.insert(user)

    print("\nTree:")
    print("-------------------------------------")
    print_tree(tree)
    print("-------------------------------------")

    traversal = rbt_inorder(tree.root, tree.NIL)
    is_sorted = all(traversal[i] < traversal[i + 1] for i in range(len(traversal) - 1))
    has_all = sorted(traversal) == sorted(users)
    root_black = not tree.root.red
    no_double_red = not has_double_red(tree.root, tree.NIL)
    consistent_bh = black_height(tree.root, tree.NIL) != -1

    passed = is_sorted and has_all and root_black and no_double_red and consistent_bh
    if not is_sorted:
        print("Fail: inorder traversal is not sorted")
    if not has_all:
        print("Fail: tree is missing inserted values")
    if not root_black:
        print("Fail: root is red")
    if not no_double_red:
        print("Fail: double red violation")
    if not consistent_bh:
        print("Fail: inconsistent black height")
    print("Pass\n" if passed else "Fail\n")
    return passed


def main():
    passed = 0
    failed = 0
    skipped = len(submit_cases) - len(test_cases)
    for test_case in test_cases:
        print("============ NEW TEST ===============")
        if test(test_case):
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


def print_tree(tree):
    lines = []
    format_tree_string(tree.root, tree.NIL, lines)
    print("\n".join(lines))


def format_tree_string(node, NIL, lines, level=0):
    if node is not None and node is not NIL:
        format_tree_string(node.right, NIL, lines, level + 1)
        color = "[red]" if node.red else "[black]"
        lines.append(" " * 4 * level + "> " + str(node.val) + " " + color)
        format_tree_string(node.left, NIL, lines, level + 1)


test_cases = submit_cases
if "__RUN__" in globals():
    test_cases = run_cases

main()
