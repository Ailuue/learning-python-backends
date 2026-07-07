"""Classic sliding-window problems.

Shared shape: a window [left, right] moves forward over the sequence carrying
running state, so every subarray question collapses into one O(n) pass. The
fixed-size flavor adds the entering element and subtracts the leaving one; the
variable-size flavor grows greedily and shrinks only when invalid.
"""


def max_sum_window(nums: list[int], k: int) -> int:
    """Max sum over all contiguous subarrays of exactly size k.

    Fixed window: compute the first window once, then slide — add the element
    entering on the right, subtract the one leaving on the left. Recomputing
    each window from scratch would be O(n*k); this is O(n).
    """
    if k <= 0 or k > len(nums):
        raise ValueError("k must be between 1 and len(nums)")
    window = sum(nums[:k])
    best = window
    for right in range(k, len(nums)):
        window += nums[right] - nums[right - k]
        best = max(best, window)
    return best


def longest_unique_substring(s: str) -> int:
    """Length of the longest substring with no repeated characters.

    Variable window. `last_seen` maps each character to the index of its most
    recent occurrence; on a repeat inside the window, jump `left` past the
    previous occurrence (no need to creep one step at a time).
    """
    last_seen: dict[str, int] = {}
    left = 0
    best = 0
    for right, char in enumerate(s):
        if char in last_seen and last_seen[char] >= left:
            left = last_seen[char] + 1  # evict the earlier duplicate
        last_seen[char] = right
        best = max(best, right - left + 1)
    return best


def longest_ones_with_flips(nums: list[int], k: int) -> int:
    """Longest run of 1s achievable by flipping at most k zeros (nums is 0/1).

    Variable window where 'valid' means 'at most k zeros inside'. Grow right;
    when a zero too many enters, advance left until one zero falls out. The
    window never shrinks below the best size found, so the final width is the
    answer even without tracking a max explicitly — but we track it for
    clarity.
    """
    left = 0
    zeros = 0
    best = 0
    for right, bit in enumerate(nums):
        if bit == 0:
            zeros += 1
        while zeros > k:
            if nums[left] == 0:
                zeros -= 1
            left += 1
        best = max(best, right - left + 1)
    return best
