# Red-Black Tree

A red-black tree is a **self-balancing binary search tree**. To understand why that matters, you first need to understand the problem it solves.

A plain binary search tree works great when the data arrives in random order — the tree stays roughly balanced and operations are fast. But if you insert data in sorted order, the tree degenerates into a chain: every node has only a right child, and you effectively end up with a slow linked list instead of a fast tree.

A red-black tree prevents this by enforcing a set of **coloring rules** after every insert: each node is painted red or black, and those colors follow strict invariants that guarantee the tree can never become too lopsided. Whenever an insert would violate the rules, the tree fixes itself automatically through rotations and recoloring. The result is a guaranteed O(log n) for every operation, no matter what order data arrives in.

The name comes from the fact that each node carries a color — red or black — and the rules governing those colors are what keep the tree balanced.

## The problem with a plain BST

Inserting sorted data into a plain BST creates a degenerate chain — effectively a linked list with O(n) operations. A red-black tree avoids this by rebalancing after every insert.

## Red-black invariants

Every valid red-black tree satisfies:

1. Every node is red or black
2. The root is black
3. `NIL` sentinel leaves are black
4. A red node's children are always black (no two consecutive reds)
5. Every path from root to a `NIL` leaf has the same number of black nodes

These invariants bound the tree height to **2 log(n+1)**, guaranteeing O(log n).

## How `_fix_insert` works

After inserting a new red node, one of three cases may arise:

| Case | Uncle colour | Fix |
|---|---|---|
| 1 | Red | Recolour parent, uncle → black; grandparent → red; move up |
| 2 | Black, node is inner child | Rotate to make it an outer child, then apply case 3 |
| 3 | Black, node is outer child | Rotate grandparent; swap colours of parent and grandparent |

## Operations

| Method | Description | Time |
|---|---|---|
| `insert(val)` | Insert a value and restore invariants | O(log n) |

*Note: `delete` is not implemented — insertion is the core learning focus here.*

## Files

| File | Contents |
|---|---|
| `red_black_tree.py` | `RBNode` and `RBTree` classes |
| `user.py` | Sample data class used in tests |
| `test_red_black_tree.py` | Invariant validation tests |

## Running tests

```bash
python test_red_black_tree.py
```
