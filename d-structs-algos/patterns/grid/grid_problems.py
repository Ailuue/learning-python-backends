"""Classic grid problems — BFS/DFS with a cell as a node and its 4 (or 8)
neighbors as edges.

The one rule that keeps these correct: mark a cell visited the instant you
enter it (DFS) or enqueue it (BFS), never when you dequeue it — otherwise the
same cell is processed more than once.
"""

from collections import deque

FOUR_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
EIGHT_DIRS = FOUR_DIRS + [(1, 1), (1, -1), (-1, 1), (-1, -1)]


def num_islands(grid: list[list[str]]) -> int:
    """Count connected regions of "1" (land) in a grid of "1"/"0" (land/water).

    DFS from each unvisited land cell, sinking the whole island to "0" so it's
    counted once. Order inside a region is irrelevant, so recursion is fine.
    """
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])

    def sink(r: int, c: int) -> None:
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] != "1":
            return
        grid[r][c] = "0"                # mark visited immediately
        for dr, dc in FOUR_DIRS:
            sink(r + dr, c + dc)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                count += 1
                sink(r, c)
    return count


def flood_fill(image: list[list[int]], sr: int, sc: int, new_color: int) -> list[list[int]]:
    """Recolor the region connected to (sr, sc) — every same-colored cell
    reachable through 4-directional steps — to new_color. (Paint bucket.)
    """
    old_color = image[sr][sc]
    if old_color == new_color:
        return image                    # guard: else infinite recursion
    rows, cols = len(image), len(image[0])

    def fill(r: int, c: int) -> None:
        if not (0 <= r < rows and 0 <= c < cols) or image[r][c] != old_color:
            return
        image[r][c] = new_color
        for dr, dc in FOUR_DIRS:
            fill(r + dr, c + dc)

    fill(sr, sc)
    return image


def rotting_oranges(grid: list[list[int]]) -> int:
    """Minutes until no fresh orange (1) is adjacent to a rotten one (2);
    -1 if some fresh orange can never rot. 0 = empty cell.

    Multi-source BFS: enqueue *every* rotten cell up front so all sources
    expand in lockstep. Each BFS layer is one minute; the last layer is the
    answer. Then check nothing fresh survived.
    """
    rows, cols = len(grid), len(grid[0])
    queue: deque[tuple[int, int]] = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c))
            elif grid[r][c] == 1:
                fresh += 1

    minutes = 0
    while queue and fresh:
        minutes += 1
        for _ in range(len(queue)):     # drain exactly one layer
            r, c = queue.popleft()
            for dr, dc in FOUR_DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2     # mark on enqueue
                    fresh -= 1
                    queue.append((nr, nc))
    return -1 if fresh else minutes


def shortest_path_binary(grid: list[list[int]]) -> int:
    """Fewest cells on a clear path from top-left to bottom-right, moving in
    any of 8 directions through 0-cells; -1 if blocked. Path length counts
    cells (a 1-cell grid of 0 has length 1).

    Shortest path -> BFS. 8-directional neighbors; the first time BFS reaches
    the corner, its layer is the minimum.
    """
    n = len(grid)
    if grid[0][0] != 0 or grid[n - 1][n - 1] != 0:
        return -1
    queue: deque[tuple[int, int, int]] = deque([(0, 0, 1)])  # (r, c, length)
    grid[0][0] = 1                      # mark visited on enqueue
    while queue:
        r, c, length = queue.popleft()
        if r == n - 1 and c == n - 1:
            return length
        for dr, dc in EIGHT_DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
                grid[nr][nc] = 1
                queue.append((nr, nc, length + 1))
    return -1
