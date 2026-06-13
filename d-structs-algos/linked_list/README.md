# Linked List

A linked list is a way to store a sequence of items where each item holds a pointer to the next one. Unlike an array, the items don't need to sit next to each other in memory — each node can be anywhere, and you find the next one by following its pointer. Think of it like a scavenger hunt: each clue tells you where the next one is hidden.

This implementation is a **singly linked list** — pointers only go in one direction (forward). It also tracks both ends of the list (head and tail), so you can add to either end instantly without walking through all the nodes first.

## How it works

Each `Node` holds a value and a `next` pointer. The list tracks `head` (front) and `tail` (back) so it can add to either end without traversal.

```
head                    tail
 │                        │
[A] → [B] → [C] → [D] → [E] → None
```

Removing from the **tail** is O(n) because there is no `prev` pointer — the list must walk forward to find the second-to-last node.

## Operations

| Method | Description | Time |
|---|---|---|
| `add_to_head(node)` | Prepend a node | O(1) |
| `add_to_tail(node)` | Append a node | O(1) |
| `remove_from_head()` | Remove and return the head node | O(1) |
| `remove_from_tail()` | Remove and return the tail node | O(n) |

## Files

| File | Contents |
|---|---|
| `node.py` | `Node` class — value and next pointer |
| `linked_list.py` | `LinkedList` class |
| `test_linked_list.py` | add/remove tests |
| `test_linked_list_remove.py` | edge cases for removal |
| `test_node.py` | Node unit tests |

## Running tests

```bash
python test_linked_list.py
```
