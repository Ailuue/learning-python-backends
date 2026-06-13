# Queue

A queue works exactly like a queue in real life — people line up, and the first person who joined the line is the first to be served. Whoever arrives first, leaves first. This "first-in, first-out" behavior is called **FIFO**.

Queues are used whenever order of arrival matters: print jobs waiting for a printer, tasks waiting to be processed by a worker, or players waiting to be matched in a game lobby. Unlike a stack (which takes from the same end it adds to), a queue adds at one end and removes from the other.

This implementation is backed by a Python list, with a practical example: a matchmaking system that pairs players as they join a lobby.

## How it works

New items are inserted at index 0 (front of the list); old items are removed from index -1 (back of the list). The oldest item is always at the back and is the next to be popped.

```
push("c") →  [c, b, a]
pop()     →  [c, b]      returns "a" (oldest)
peek()    →  [c, b]      returns "b" (next to pop)
```

> Note: `push` uses `list.insert(0, item)` which is O(n). A `collections.deque` would give O(1) push, but this implementation keeps the code simple for learning purposes.

## Operations

| Method | Description | Time |
|---|---|---|
| `push(item)` | Enqueue an item | O(n) |
| `pop()` | Dequeue the oldest item (`None` if empty) | O(1) |
| `peek()` | Return next item without removing | O(1) |
| `size()` | Number of items | O(1) |
| `search_and_remove(item)` | Find and remove a specific item | O(n) |

## Application — matchmaking (`matchmake.py`)

Simulates a game lobby queue:
- `"join"` → push player onto the queue
- `"leave"` → `search_and_remove` the player by name
- When 4+ players are in the queue → pop two and announce a match

```python
matchmake(queue, ("Alice", "join"))   # "No match found"
matchmake(queue, ("Bob",   "join"))   # "No match found"
matchmake(queue, ("Carol", "join"))   # "No match found"
matchmake(queue, ("Dave",  "join"))   # "Alice matched Bob!"
```

## Files

| File | Contents |
|---|---|
| `custom_queue.py` | `Queue` class |
| `matchmake.py` | `matchmake(queue, user)` function |
| `test_queue.py` | Queue unit tests |
| `test_matchmake.py` | Matchmaking scenario tests |

## Running tests

```bash
python test_queue.py
python test_matchmake.py
```
