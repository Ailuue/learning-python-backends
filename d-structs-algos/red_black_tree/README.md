# Red-Black Tree

A self-balancing BST that guarantees O(log n) insert regardless of insertion order.

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
