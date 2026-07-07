"""Classic two-pointer problems.

Shared idea: use a property of the input (sortedness, symmetry) to prove that
moving one pointer can never miss the answer — that proof is what collapses a
nested scan into a single pass, and it's the part to be able to say out loud.
"""


def pair_sum_sorted(nums: list[int], target: int) -> tuple[int, int] | None:
    """Indices (i, j), i < j, with nums[i] + nums[j] == target; None if absent.

    Requires nums sorted ascending. If the current sum is too small, no pair
    using this `left` can work (right is already the largest partner) — so
    left++ discards them all at once. Symmetric for too-big.
    """
    left, right = 0, len(nums) - 1
    while left < right:
        total = nums[left] + nums[right]
        if total == target:
            return (left, right)
        if total < target:
            left += 1
        else:
            right -= 1
    return None


def most_water(heights: list[int]) -> int:
    """Max area between two walls: area = min(h[i], h[j]) * (j - i).

    Converge from the ends, always moving the *shorter* wall: the area is
    capped by the shorter wall, so moving the taller one can only shrink the
    width without raising the cap — it can never help.
    """
    left, right = 0, len(heights) - 1
    best = 0
    while left < right:
        best = max(best, min(heights[left], heights[right]) * (right - left))
        if heights[left] <= heights[right]:
            left += 1
        else:
            right -= 1
    return best


def is_palindrome_alnum(s: str) -> bool:
    """True if s reads the same both ways, ignoring case and non-alphanumerics."""
    left, right = 0, len(s) - 1
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
        if s[left].lower() != s[right].lower():
            return False
        left += 1
        right -= 1
    return True


def three_sum(nums: list[int]) -> list[tuple[int, int, int]]:
    """All unique triples (a, b, c), a <= b <= c, with a + b + c == 0.

    Sort, then for each fixed first value run the pair_sum converge on the
    remainder. The duplicate-skipping is what interviews actually test here:
    skip repeated first values, and after a hit, skip repeated seconds/thirds.
    """
    nums = sorted(nums)
    triples: list[tuple[int, int, int]] = []
    for i in range(len(nums) - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue  # same first value as last iteration -> same triples
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                triples.append((nums[i], nums[left], nums[right]))
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
    return triples
