# Monotonic Stack Problems

A **monotonic stack** is an ordinary [stack](../../stack/) with one rule: you
keep it sorted (always increasing, or always decreasing) by **popping anything
that would break the order before you push**. That single discipline answers a
whole family of "for each element, find the next/previous element that is
bigger/smaller" questions in one O(n) pass instead of the obvious O(n²) double
loop.

## The signal

The problem asks, for every element, about the **nearest larger or smaller
element** to one side: "next warmer day," "next greater element," "how far until
a taller bar," "largest rectangle under a histogram," "how much rain is trapped."
If you catch yourself writing "for each i, scan forward until I find something
bigger," that inner scan is what the stack eliminates.

Why it's O(n) despite the nested-looking `while`: each element is **pushed once
and popped once**, so the total pop work across the whole run is n, not n per
element. That amortized argument is the thing to say out loud.

The template (this one finds the next *greater* element to the right):

```
stack = []                      # holds indices, values decreasing bottom->top
for i, x in enumerate(nums):
    while stack and nums[stack[-1]] < x:
        j = stack.pop()         # x is the answer for element j
        answer[j] = x
    stack.append(i)
# anything left on the stack has no greater element to its right
```

Decreasing stack → next greater; increasing stack → next smaller. Push the
**index** (not the value) when you need distances.

## The problems ([monotonic_problems.py](monotonic_problems.py))

| Problem | Stack keeps | Answers |
|---|---|---|
| `next_greater` | decreasing | next strictly greater value to the right (-1 if none) |
| `daily_temperatures` | decreasing (indices) | days to wait for a warmer temperature |
| `largest_rectangle` | increasing (indices) | biggest area in a histogram |
| `trapping_rain_water` | decreasing (indices) | total water trapped between bars |

`largest_rectangle` is the hard one interviewers reach for — the "pop until
smaller, and the popped bar's width spans from the new top to here" bookkeeping
is worth deriving slowly once.
