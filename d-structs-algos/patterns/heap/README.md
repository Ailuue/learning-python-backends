# Heap (Priority Queue) Problems

A **heap** is a tree-shaped structure (stored flat in a list) that keeps the
smallest element at the root at all times. Insert and remove-smallest are both
O(log n), and reading the smallest is O(1). Python's [`heapq`](https://docs.python.org/3/library/heapq.html)
is a min-heap over a plain list; there is no max-heap variant, so the standard
trick is to **negate the values** (a max becomes a min of negatives).

## The signal

Any problem that says **"the k largest / smallest / most frequent / closest"**
is a heap problem. The trap it's testing: sorting everything costs
O(n log n), but you only need k of the items — a heap of size k gets the answer
in **O(n log k)**, and for streaming data it's the only option (you never hold
all n items).

The counter-intuitive detail interviewers probe: to find the k **largest**
items, keep a **min**-heap of size k. The root is always the *weakest of your
current best k* — every new item only has to beat that one element to earn a
slot. (Symmetrically: k smallest → max-heap of size k.)

## The problems ([heap_problems.py](heap_problems.py))

| Problem | The lesson |
|---|---|
| `kth_largest` | The size-k min-heap invariant, in its purest form |
| `top_k_frequent` | Count first (hashmap), then heap over the counts — two structures composed |
| `k_closest_points` | The heap key is whatever the problem's "value" is — here, a distance |

Complexities: all O(n log k) time, O(k) extra space (plus the counter's O(n)
for `top_k_frequent`).
