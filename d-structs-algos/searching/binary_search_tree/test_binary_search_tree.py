from binary_search_tree import *
from user import *

# ── insert + inorder (sorted property) ───────────────────────────────────────

run_cases = [
    (3),
    (5),
]

submit_cases = run_cases + [
    (10),
]

# ── traversals: tree [5,3,7,1,4,6,8] ─────────────────────────────────────────
#
#          5
#         / \
#        3   7
#       / \ / \
#      1  4 6  8

BALANCED = [5, 3, 7, 1, 4, 6, 8]

traversal_run_cases = [
    (BALANCED, "inorder",   [1, 3, 4, 5, 6, 7, 8]),
    (BALANCED, "preorder",  [5, 3, 1, 4, 7, 6, 8]),
    (BALANCED, "postorder", [1, 4, 3, 6, 8, 7, 5]),
]

traversal_submit_cases = traversal_run_cases + [
    ([5, 3, 7], "inorder",   [3, 5, 7]),
    ([5, 3, 7], "preorder",  [5, 3, 7]),
    ([5, 3, 7], "postorder", [3, 7, 5]),
]

# ── delete ────────────────────────────────────────────────────────────────────

delete_run_cases = [
    (BALANCED, 1, [3, 4, 5, 6, 7, 8]),   # delete leaf
    (BALANCED, 3, [1, 4, 5, 6, 7, 8]),   # delete node with two children
    (BALANCED, 5, [1, 3, 4, 6, 7, 8]),   # delete root
]

delete_submit_cases = delete_run_cases + [
    (BALANCED, 7, [1, 3, 4, 5, 6, 8]),   # delete right subtree root
    ([5, 3], 3, [5]),                      # delete only child
]

# ── exists ────────────────────────────────────────────────────────────────────

exists_run_cases = [
    (BALANCED, 3, True),
    (BALANCED, 9, False),
]

exists_submit_cases = exists_run_cases + [
    (BALANCED, 1, True),
    (BALANCED, 8, True),
    (BALANCED, 0, False),
]

# ── height ────────────────────────────────────────────────────────────────────

height_run_cases = [
    (BALANCED, 3),        # balanced tree
    ([5], 1),             # single node
]

height_submit_cases = height_run_cases + [
    ([5, 3, 1], 3),       # left-leaning chain
    ([5, 7, 9], 3),       # right-leaning chain
    ([5, 3, 7, 1], 3),    # unbalanced but still depth 3
]


def build_bst(vals):
    bst = binary_search_tree_node()
    for v in vals:
        bst.insert(v)
    return bst


# ── test functions ────────────────────────────────────────────────────────────

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


def test_traversal(vals, order, expected):
    bst = build_bst(vals)
    if order == "inorder":
        result = bst.inorder()
    elif order == "preorder":
        result = bst.preorder([])
    else:
        result = bst.postorder([])
    ok = result == expected
    print(f"  {order}({vals}) → {result} {'✓' if ok else '✗ expected ' + str(expected)}")
    return ok


def test_delete(vals, target, expected_inorder):
    bst = build_bst(vals)
    bst.delete(target)
    result = bst.inorder()
    ok = result == expected_inorder
    print(f"  delete({target}) from {vals} → inorder {result} {'✓' if ok else '✗ expected ' + str(expected_inorder)}")
    return ok


def test_exists(vals, target, expected):
    bst = build_bst(vals)
    result = bst.exists(target)
    ok = result == expected
    print(f"  exists({target}) in {vals} → {result} {'✓' if ok else '✗ expected ' + str(expected)}")
    return ok


def test_height(vals, expected):
    bst = build_bst(vals)
    result = bst.height()
    ok = result == expected
    print(f"  height({vals}) → {result} {'✓' if ok else '✗ expected ' + str(expected)}")
    return ok


def run_section(name, cases, fn):
    print(f"──── {name} ────────────────────────")
    passed = failed = 0
    for case in cases:
        if fn(*case):
            passed += 1
        else:
            failed += 1
    return passed, failed


def main() -> None:
    total_passed = total_failed = 0

    print("──── insert + inorder ──────────────")
    skipped = len(submit_cases) - len(insert_cases)
    for case in insert_cases:
        print("=====================================")
        if test(case):
            total_passed += 1
        else:
            total_failed += 1

    for name, cases, fn in [
        ("traversals", traversal_cases, test_traversal),
        ("delete", delete_cases, test_delete),
        ("exists", exists_cases, test_exists),
        ("height", height_cases, test_height),
    ]:
        p, f = run_section(name, cases, fn)
        total_passed += p
        total_failed += f

    if total_failed == 0:
        print("============= PASS ==============")
    else:
        print("============= FAIL ==============")
    if skipped > 0:
        print(f"{total_passed} passed, {total_failed} failed, {skipped} skipped")
    else:
        print(f"{total_passed} passed, {total_failed} failed")


def print_tree(bst_node: binary_search_tree_node):
    lines = []
    format_tree_string(bst_node, lines)
    print("\n".join(lines))


def format_tree_string(bst_node: binary_search_tree_node | None, lines: list, level: int = 0):
    if bst_node is not None:
        format_tree_string(bst_node.right, lines, level + 1)
        lines.append(" " * 4 * level + "> " + str(bst_node.val))
        format_tree_string(bst_node.left, lines, level + 1)


if "__RUN__" in globals():
    insert_cases = run_cases
    traversal_cases = traversal_run_cases
    delete_cases = delete_run_cases
    exists_cases = exists_run_cases
    height_cases = height_run_cases
else:
    insert_cases = submit_cases
    traversal_cases = traversal_submit_cases
    delete_cases = delete_submit_cases
    exists_cases = exists_submit_cases
    height_cases = height_submit_cases

main()
