"""Trie (prefix-tree) interview problems.

The structure itself is built from scratch in ../../prefix_tree/; this module is
about the *pattern* — the questions where a trie collapses "compare the query
against every word" into one walk down shared prefixes. Nodes are plain dicts of
child-char -> node, with a sentinel key marking a complete word.
"""

END = "$"  # sentinel key in a node's dict marking the end of a stored word


class Trie:
    """The baseline prefix tree (LeetCode 208)."""

    def __init__(self) -> None:
        self.root: dict = {}

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node[END] = True

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and END in node

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def _walk(self, s: str) -> dict | None:
        node = self.root
        for ch in s:
            if ch not in node:
                return None
            node = node[ch]
        return node


class WordDictionary:
    """A trie whose search supports '.' as a wildcard for any single letter
    (LeetCode 211). The dot is what forces a *search* of the trie rather than a
    single walk — at a dot, every child branch must be tried.
    """

    def __init__(self) -> None:
        self.root: dict = {}

    def add(self, word: str) -> None:
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node[END] = True

    def search(self, word: str) -> bool:
        def dfs(node: dict, i: int) -> bool:
            if i == len(word):
                return END in node
            ch = word[i]
            if ch == ".":
                return any(
                    dfs(child, i + 1)
                    for key, child in node.items()
                    if key != END        # END maps to True, not a node
                )
            return ch in node and dfs(node[ch], i + 1)

        return dfs(self.root, 0)


def replace_words(dictionary: list[str], sentence: str) -> str:
    """Replace every word in `sentence` by the shortest dictionary 'root' that
    is a prefix of it; leave it unchanged if no root applies (LeetCode 648).

    Build a trie of the roots, then for each word walk it and stop at the first
    END — that's the shortest matching root.
    """
    trie = Trie()
    for root in dictionary:
        trie.insert(root)

    def shortest_root(word: str) -> str:
        node = trie.root
        for i, ch in enumerate(word):
            if ch not in node:
                break
            node = node[ch]
            if END in node:
                return word[: i + 1]      # shortest prefix that is a full root
        return word

    return " ".join(shortest_root(w) for w in sentence.split())


def find_words_on_board(board: list[list[str]], words: list[str]) -> list[str]:
    """Every word from `words` that can be spelled on the board by stepping
    between 4-directional neighbors without reusing a cell (LeetCode 212).

    One trie of all the words + one DFS over the board: at each cell we only
    recurse down trie branches that match, so a dead prefix prunes instantly —
    far cheaper than running a single-word search once per word.
    """
    trie = Trie()
    for word in words:
        trie.insert(word)

    rows, cols = len(board), len(board[0])
    found: set[str] = set()

    def dfs(r: int, c: int, node: dict, path: str) -> None:
        if END in node:
            found.add(path)               # don't return — a longer word may extend it
        if not (0 <= r < rows and 0 <= c < cols):
            return
        ch = board[r][c]
        if ch not in node:
            return                        # prefix not in any word -> prune
        board[r][c] = "#"                 # mark visited
        child = node[ch]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            dfs(r + dr, c + dc, child, path + ch)
        board[r][c] = ch                  # restore

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, trie.root, "")
    return sorted(found)
