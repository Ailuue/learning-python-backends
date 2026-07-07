# Interval Problems

An **interval** is a `[start, end]` pair — a meeting, a booking, a range on a
number line. Interval problems ask you to reason about how a pile of them
overlaps, and almost all of them start with the same move: **sort by start
time**. Once sorted, overlaps become local — you only ever have to compare each
interval with the one you're currently holding, never with all the others.

## The signal

The input is a list of `[start, end]` pairs and the question is about
**overlap, merging, or scheduling**: "merge the overlapping ones," "insert a new
booking," "can one person attend all these meetings," "how many rooms do you
need at once." If you catch yourself about to compare every pair against every
other pair (O(n²)), stop — sorting first almost always drops it to O(n log n).

Two overlap tests worth memorizing:

- Two intervals `a`, `b` **overlap** iff `a.start <= b.end and b.start <= a.end`.
- After sorting by start, a new interval overlaps the one you're merging iff
  `new.start <= current.end` — you only need the running `current.end`.

The subtler family — "how many resources are needed at peak" (meeting rooms II) —
uses a different trick: split each interval into a `+1` start event and a `-1`
end event, sort the events, and sweep. The running sum's maximum is the answer.
That **sweep line** idea generalizes far beyond intervals.

## The problems ([interval_problems.py](interval_problems.py))

| Problem | Move |
|---|---|
| `merge_intervals` | sort by start; extend or append against a running `current` |
| `insert_interval` | before / overlap / after — merge the overlap span in one pass |
| `can_attend_all` | sort; any `next.start < prev.end` means a clash |
| `min_meeting_rooms` | sweep line over +1/-1 events; track the running max |

Complexities: all O(n log n) from the sort; the passes themselves are O(n).
