# Stack

An array-backed LIFO (last-in, first-out) stack, plus a practical application: balanced bracket checking.

## How it works

Items are pushed onto and popped from the same end — the "top". The underlying `list` makes all operations O(1).

```
push("c") →  [a, b, c]  ← top
pop()     →  [a, b]      returns "c"
peek()    →  [a, b]      returns "b" (no removal)
```

## Operations

| Method | Description | Time |
|---|---|---|
| `push(item)` | Add to top | O(1) |
| `pop()` | Remove and return top item (`None` if empty) | O(1) |
| `peek()` | Return top item without removing | O(1) |
| `size()` | Number of items | O(1) |

## Application — balanced brackets (`balanced.py`)

Uses the stack to check whether parentheses are balanced:
- `(` → push onto stack
- `)` → pop; if stack is empty, return `False` (unmatched closing bracket)
- At the end: balanced if and only if the stack is empty

```python
is_balanced("(a(b)c)")  # True
is_balanced("(a(b)c")   # False — unclosed bracket
is_balanced("a)b(c")    # False — closing before opening
```

## Files

| File | Contents |
|---|---|
| `stack.py` | `Stack` class |
| `balanced.py` | `is_balanced(input_str)` function |
| `test_stack.py` | Stack unit tests |
| `test_balanced.py` | Balanced bracket tests |

## Running tests

```bash
python test_stack.py
python test_balanced.py
```
