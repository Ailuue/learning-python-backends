# Binary Search Tree

A binary search tree (BST) organizes data so that every search decision is simple: at each node, go left if the value you're looking for is smaller, or go right if it's larger. This rule is enforced everywhere in the tree — every node's left subtree contains only smaller values, and its right subtree contains only larger ones.

The result is that you can find, insert, or delete any value by making one left-or-right decision per level and ignoring the entire other half of the tree each time. It's the same idea as binary search on a sorted array, but in a tree structure that also supports fast insertions and deletions.

BSTs are a foundational concept that leads directly to more advanced self-balancing trees like the [Red-Black Tree](../../red_black_tree/).

## How it works

**Invariant:** `left.val < node.val ≤ right.val` at every node.

This means search, insert, and delete can all skip half the tree at each step — O(log n) on average. A degenerate tree (inserting sorted data) degrades to O(n); use a [Red-Black Tree](../../red_black_tree/) for a guaranteed O(log n).

## Operations

| Method | Description | Time (avg) |
|---|---|---|
| `insert(val)` | Add a value | O(log n) |
| `exists(val)` | Check for a value | O(log n) |
| `delete(val)` | Remove a value | O(log n) |
| `height()` | Height of the tree | O(n) |
| `inorder()`  | Left → root → right (sorted order) | O(n) |
| `preorder()` | Root → left → right | O(n) |
| `postorder()` | Left → right → root | O(n) |

### Deletion — two-children case

When deleting a node with two children, the implementation replaces the node's value with its **in-order successor** (the minimum value in the right subtree), then deletes that successor from the right subtree.

```
Delete 5 from:        Result:
      5                   6
     / \                 / \
    3   8               3   8
       /                   /
      6                   7
       \
        7
```

## Traversal order

```
Tree:      4
          / \
         2   6
        / \ / \
       1  3 5  7

inorder:   [1, 2, 3, 4, 5, 6, 7]  ← sorted
preorder:  [4, 2, 1, 3, 6, 5, 7]  ← root first
postorder: [1, 3, 2, 5, 7, 6, 4]  ← root last
```

## Files

| File | Contents |
|---|---|
| `binary_search_tree.py` | `binary_search_tree_node` class |
| `user.py` | Sample data class used in tests |
| `test_binary_search_tree.py` | Unit tests |

## Running tests

```bash
python test_binary_search_tree.py
```
