"""Monotonic-stack problems: keep a stack sorted by popping anything that
breaks the order before pushing, and 'nearest larger/smaller element' questions
fall out in one O(n) pass.

The amortized argument that makes the nested while-loop still O(n): every index
is pushed once and popped once, so total pop work is n across the whole run.
"""


def next_greater(nums: list[int]) -> list[int]:
    """For each element, the next strictly greater value to its right, or -1.

    Decreasing stack of indices: when a new value is bigger than the value at
    the top, it's that top element's answer — pop and record, repeat.
    """
    result = [-1] * len(nums)
    stack: list[int] = []                 # indices; values decrease bottom->top
    for i, x in enumerate(nums):
        while stack and nums[stack[-1]] < x:
            result[stack.pop()] = x
        stack.append(i)
    return result                          # leftovers keep their -1


def daily_temperatures(temps: list[int]) -> list[int]:
    """For each day, how many days until a warmer one; 0 if none follows.

    Same decreasing stack, but the answer is a *distance*, so store indices and
    subtract when you resolve one.
    """
    result = [0] * len(temps)
    stack: list[int] = []
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            result[j] = i - j              # days waited
        stack.append(i)
    return result


def largest_rectangle(heights: list[int]) -> int:
    """Area of the largest rectangle that fits under a histogram.

    Increasing stack of indices. When the incoming bar is shorter than the top,
    that top bar can't extend further right — pop it and compute its widest
    rectangle: its height times the span from the new stack top (its left
    boundary) to the current index (its right boundary). A trailing sentinel of
    height 0 flushes everything left on the stack at the end.
    """
    stack: list[int] = []                  # indices; heights increase bottom->top
    best = 0
    for i, h in enumerate(heights + [0]):  # sentinel forces a final flush
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            left = stack[-1] if stack else -1
            width = i - left - 1           # span between the two shorter bars
            best = max(best, height * width)
        stack.append(i)
    return best


def trapping_rain_water(heights: list[int]) -> int:
    """Total water trapped between bars after rain.

    Decreasing stack of indices. When a taller bar arrives, it and the bar
    below the popped one form a container over the dip: water = width * bounded
    height, where the height is capped by the shorter of the two walls minus
    the floor being filled.
    """
    stack: list[int] = []
    water = 0
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] < h:
            floor = heights[stack.pop()]
            if not stack:
                break                       # no left wall -> water runs off
            left = stack[-1]
            width = i - left - 1
            bounded = min(heights[left], h) - floor
            water += width * bounded
        stack.append(i)
    return water
