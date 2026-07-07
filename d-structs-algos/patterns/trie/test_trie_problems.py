from trie_problems import Trie, WordDictionary, find_words_on_board, replace_words


def trie_ops() -> tuple:
    """insert 'apple', then exercise exact search vs prefix search."""
    t = Trie()
    t.insert("apple")
    return (
        t.search("apple"),      # True: exact word
        t.search("app"),        # False: a prefix, not a stored word
        t.starts_with("app"),   # True: prefix exists
        t.starts_with("apx"),   # False
    )


def word_dictionary_ops() -> tuple:
    """add a few words, then search with '.' wildcards."""
    d = WordDictionary()
    for w in ("bad", "dad", "mad"):
        d.add(w)
    return (
        d.search("pad"),    # False
        d.search("bad"),    # True: exact
        d.search(".ad"),    # True: matches all three
        d.search("b.."),    # True: matches 'bad'
        d.search("..."),    # True
        d.search("...."),   # False: no 4-letter word
    )


cases = [
    (trie_ops, (), (True, False, True, False)),
    (word_dictionary_ops, (), (False, True, True, True, True, False)),
    (replace_words, (["cat", "bat", "rat"], "the cattle was rattled by the battery"),
        "the cat was rat by the bat"),
    (replace_words, (["a", "b", "c"], "aadsfasf absbs bbab cadsfafs"),
        "a a b c"),
    (replace_words, (["catt", "cat"], "the cattle"),          # shortest root wins
        "the cat"),
    (find_words_on_board, ([["o", "a", "a", "n"],
                            ["e", "t", "a", "e"],
                            ["i", "h", "k", "r"],
                            ["i", "f", "l", "v"]],
                           ["oath", "pea", "eat", "rain"]),
        ["eat", "oath"]),
    (find_words_on_board, ([["a", "b"], ["c", "d"]], ["abcb"]), []),  # no cell reuse
    (find_words_on_board, ([["a"]], ["a", "aa"]), ["a"]),
]


def test(func, args, expected) -> bool:
    print("---------------------------------")
    print(f"{func.__name__}{args}")
    print(f"Expected: {expected}")
    result = func(*args)
    print(f"Actual:   {result}")
    if result == expected:
        print("Pass")
        return True
    print("Fail")
    return False


def main() -> None:
    passed = 0
    failed = 0
    for func, args, expected in cases:
        if test(func, args, expected):
            passed += 1
        else:
            failed += 1
    print("=================================")
    print(f"{passed} passed, {failed} failed")


main()
