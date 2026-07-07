"""Binary search beyond a sorted array.

The first two search array indices in a *rotated* sorted array (one half of any
slice is always sorted, so you can still halve each step). The last two search
the space of *answers* — a speed, a capacity — using a monotonic feasibility
check, with no sorted array in sight. That leap is the pattern.
"""

import math


def search_rotated(nums: list[int], target: int) -> int:
    """Index of target in a rotated sorted array of distinct values, or -1.

    At each step one side of [lo, hi] is sorted. Figure out which (compare
    nums[lo] to nums[mid]); if target lies within that sorted side's range,
    search it, else search the other side.
    """
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:               # left half is sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:                                   # right half is sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


def find_min_rotated(nums: list[int]) -> int:
    """Minimum value of a rotated sorted array of distinct values.

    The minimum is the pivot. If nums[mid] > nums[hi], the pivot is to mid's
    right; otherwise mid could be the pivot, so keep it. Converge to it.
    """
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1                        # pivot is strictly right of mid
        else:
            hi = mid                            # pivot is mid or left of it
    return nums[lo]


def min_eating_speed(piles: list[int], hours: int) -> int:
    """Smallest integer eating speed (bananas/hour) to finish all piles within
    `hours` hours; you eat from one pile per hour, leftovers count as a full
    hour. Binary search the *speed*, not any array.

    feasible(speed) = total hours needed at this speed <= hours. It's
    monotonic: faster is never slower, so answers look False...False True...True.
    """
    def hours_needed(speed: int) -> int:
        return sum(math.ceil(pile / speed) for pile in piles)

    lo, hi = 1, max(piles)                      # speed range: 1 .. biggest pile
    while lo < hi:
        mid = (lo + hi) // 2
        if hours_needed(mid) <= hours:
            hi = mid                            # mid works; try slower
        else:
            lo = mid + 1                        # too slow; must go faster
    return lo


def ship_within_days(weights: list[int], days: int) -> int:
    """Least ship capacity to deliver all packages (in given order) within
    `days` days. Binary search the *capacity*.

    Search space: max(weights) (a package must fit) .. sum(weights) (one day).
    feasible(cap) = greedily packing without exceeding cap fits in <= days.
    """
    def days_needed(cap: int) -> int:
        used = 1
        load = 0
        for weight in weights:
            if load + weight > cap:
                used += 1                       # start a new day
                load = 0
            load += weight
        return used

    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = (lo + hi) // 2
        if days_needed(mid) <= days:
            hi = mid
        else:
            lo = mid + 1
    return lo
