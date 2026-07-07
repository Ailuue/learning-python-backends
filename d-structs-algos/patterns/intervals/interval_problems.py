"""Classic interval problems. The shared first move is 'sort by start time',
which makes overlaps local — each interval only ever compares against the one
you're currently holding, never all the others.
"""


def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    """Merge all overlapping intervals into the minimal set of disjoint ones.

    Sort by start, then walk: if the next interval starts at or before the
    current one's end, they touch — extend the current end. Otherwise the
    current interval is finished, so append it and start a new one.
    """
    if not intervals:
        return []
    intervals = sorted(intervals, key=lambda pair: pair[0])
    merged = [intervals[0][:]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)  # overlap: extend
        else:
            merged.append([start, end])              # gap: new interval
    return merged


def insert_interval(intervals: list[list[int]], new: list[int]) -> list[list[int]]:
    """Insert `new` into an already-sorted, non-overlapping list, keeping the
    result sorted and merged. One O(n) pass, three phases:

      1. intervals entirely before `new` — copy as-is
      2. intervals overlapping `new` — absorb into `new`'s span
      3. intervals entirely after `new` — copy as-is
    """
    result: list[list[int]] = []
    start, end = new
    i, n = 0, len(intervals)

    while i < n and intervals[i][1] < start:         # phase 1: strictly before
        result.append(intervals[i])
        i += 1
    while i < n and intervals[i][0] <= end:          # phase 2: overlapping
        start = min(start, intervals[i][0])
        end = max(end, intervals[i][1])
        i += 1
    result.append([start, end])
    while i < n:                                     # phase 3: strictly after
        result.append(intervals[i])
        i += 1
    return result


def can_attend_all(meetings: list[list[int]]) -> bool:
    """True if one person can attend every meeting (no two overlap).

    Sort by start; a clash exists iff some meeting starts before the previous
    one ends. Touching ends ([1,2] then [2,3]) don't clash.
    """
    meetings = sorted(meetings, key=lambda pair: pair[0])
    for i in range(1, len(meetings)):
        if meetings[i][0] < meetings[i - 1][1]:
            return False
    return True


def min_meeting_rooms(meetings: list[list[int]]) -> int:
    """Fewest rooms so no two meetings share a room — the max number that
    overlap at any instant.

    Sweep line: turn each meeting into a +1 event at its start and a -1 at its
    end, sort the events (ends before starts at the same time, so a room frees
    up before the next meeting claims it), then track the running max.
    """
    events: list[tuple[int, int]] = []
    for start, end in meetings:
        events.append((start, 1))    # a room is needed
        events.append((end, -1))     # a room frees up
    # Sort by time; at equal times, process -1 (end) before +1 (start).
    events.sort(key=lambda e: (e[0], e[1]))
    rooms = 0
    peak = 0
    for _, delta in events:
        rooms += delta
        peak = max(peak, rooms)
    return peak
