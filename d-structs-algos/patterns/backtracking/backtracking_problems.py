"""Classic backtracking problems, each a variation of one skeleton:
choose -> recurse -> un-choose, with pruning where a branch is hopeless.

The shared discipline: mutate a single `path` in place and copy it only when
recording a complete solution, so exploring the whole decision tree stays cheap.
"""


def subsets(nums: list[int]) -> list[list[int]]:
    """Every subset (the power set) of a distinct-element list.

    Choice at index i: the recursion at `start` decides, for each later
    element, whether to include it. Advancing `start` (not restarting at 0) is
    what stops [1,2] and [2,1] from both appearing — subsets are unordered.
    """
    result: list[list[int]] = []

    def backtrack(start: int, path: list[int]) -> None:
        result.append(path[:])          # every node is a valid subset; copy it
        for i in range(start, len(nums)):
            path.append(nums[i])        # choose nums[i]
            backtrack(i + 1, path)      # future choices come after i
            path.pop()                  # un-choose

    backtrack(0, [])
    return result


def permutations(nums: list[int]) -> list[list[int]]:
    """Every ordering of a distinct-element list.

    Unlike subsets, order matters and every element must appear, so the choice
    is 'which unused element goes in the next slot' — a `used` flag tracks
    what's already placed on the current path.
    """
    result: list[list[int]] = []
    used = [False] * len(nums)

    def backtrack(path: list[int]) -> None:
        if len(path) == len(nums):
            result.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue                # prune: already on this path
            used[i] = True
            path.append(nums[i])
            backtrack(path)
            path.pop()
            used[i] = False

    backtrack([])
    return result


def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    """All multisets of candidates (each reusable) that sum to target.

    Sorted-unique output. Two prunes: stop the moment the remaining target goes
    negative, and pass `i` (not i+1) so the same candidate can repeat while
    still never producing a permutation of an earlier combination.
    """
    result: list[list[int]] = []
    candidates = sorted(candidates)

    def backtrack(start: int, remaining: int, path: list[int]) -> None:
        if remaining == 0:
            result.append(path[:])
            return
        for i in range(start, len(candidates)):
            if candidates[i] > remaining:
                break                   # sorted: nothing later fits either
            path.append(candidates[i])
            backtrack(i, remaining - candidates[i], path)  # i -> reuse allowed
            path.pop()

    backtrack(0, target, [])
    return result


def word_search(board: list[list[str]], word: str) -> bool:
    """True if `word` can be spelled by stepping between adjacent cells
    (up/down/left/right) without reusing a cell.

    Backtracking on a grid: mark a cell visited before recursing into its
    neighbors, then restore it on the way out so other paths can use it.
    """
    if not board or not board[0]:
        return False
    rows, cols = len(board), len(board[0])

    def backtrack(r: int, c: int, i: int) -> bool:
        if i == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[i]:
            return False
        board[r][c] = "#"               # mark visited (choose)
        found = (
            backtrack(r + 1, c, i + 1)
            or backtrack(r - 1, c, i + 1)
            or backtrack(r, c + 1, i + 1)
            or backtrack(r, c - 1, i + 1)
        )
        board[r][c] = word[i]           # restore (un-choose)
        return found

    return any(backtrack(r, c, 0) for r in range(rows) for c in range(cols))
