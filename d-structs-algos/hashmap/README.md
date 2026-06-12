# HashMap

An open-addressing hash map with linear probing and automatic resizing.

## How it works

### Hashing
The key is converted to an index by summing the ASCII values of its characters and taking the result modulo the table size:

```python
index = sum(ord(c) for c in key) % len(table)
```

### Collision resolution — linear probing
If the target slot is occupied by a different key, the map steps forward one slot at a time (wrapping around) until it finds an empty slot or the same key.

```
insert("cat"):  hash → slot 3  (empty → place here)
insert("act"):  hash → slot 3  (occupied by "cat") → try slot 4 → empty → place here
```

### Auto-resize
Before every `insert`, the load factor (filled slots / total slots) is checked. If it reaches **70%**, the table doubles and all existing entries are re-inserted:

```
load = 0.69 → insert normally
load = 0.70 → double the table, re-hash everything, then insert
```

## Operations

| Method | Description | Time (average) |
|---|---|---|
| `insert(key, value)` | Store a key-value pair | O(1) |
| `get(key)` | Retrieve a value by key | O(1) |
| `current_load()` | Fraction of slots currently filled | O(n) |
| `resize()` | Double table and re-insert (called automatically) | O(n) |

## Files

| File | Contents |
|---|---|
| `hashmap.py` | `HashMap` class |
| `test_hashmap.py` | Unit tests |

## Running tests

```bash
python test_hashmap.py
```
