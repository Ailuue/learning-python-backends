"""Classic heap problems, each solved the canonical size-k way.

The shared idea: never sort all n items to get k of them. Maintain a heap of
size k whose root is the weakest member of the current best-k; each new item
only competes against that root. O(n log k) beats O(n log n) whenever k << n,
and it's the only shape that works on a stream.
"""

import heapq
from collections import Counter


def kth_largest(nums: list[int], k: int) -> int:
    """Return the kth largest value (k=1 means the maximum).

    Min-heap of size k: after pushing everything through, the root is the
    kth largest — the smallest of the k best.
    """
    heap: list[int] = []
    for num in nums:
        if len(heap) < k:
            heapq.heappush(heap, num)
        elif num > heap[0]:
            heapq.heapreplace(heap, num)  # pop the weakest, push the newcomer
    return heap[0]


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    """Return the k most frequent values, most frequent first.

    Ties break toward the smaller value, so the output is deterministic.
    Two structures composed: a Counter to get (value, count) pairs, then the
    same size-k heap idea over the counts.
    """
    counts = Counter(nums)
    # Heap entries are (count, -value): the weakest is the lowest count, and
    # among equal counts the *larger* value (so smaller values survive ties).
    heap: list[tuple[int, int]] = []
    for value, count in counts.items():
        entry = (count, -value)
        if len(heap) < k:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)
    # Pop yields weakest-first; reverse for most-frequent-first.
    ordered = [heapq.heappop(heap) for _ in range(len(heap))][::-1]
    return [-neg_value for _, neg_value in ordered]


def k_closest_points(points: list[tuple[int, int]], k: int) -> list[tuple[int, int]]:
    """Return the k points closest to the origin, closest first.

    Same invariant with the sign flipped: we want the k *smallest* distances,
    so the heap holds negated distances — its root is the *farthest* of the
    current best k, the one a newcomer must beat.
    """
    heap: list[tuple[int, tuple[int, int]]] = []
    for x, y in points:
        entry = (-(x * x + y * y), (x, y))
        if len(heap) < k:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:  # less negative = closer than the current farthest
            heapq.heapreplace(heap, entry)
    ordered = [heapq.heappop(heap) for _ in range(len(heap))][::-1]
    return [point for _, point in ordered]
