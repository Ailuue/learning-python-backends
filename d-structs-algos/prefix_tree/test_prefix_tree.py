from prefix_tree import *

# ── exists ────────────────────────────────────────────────────────────────────

exists_run_cases = [
    (["apple", "app", "banana"], "apple", True),
    (["apple", "app", "banana"], "app", True),
    (["apple", "app", "banana"], "ap", False),   # prefix only, not a word
    (["apple", "app", "banana"], "grape", False),
]

exists_submit_cases = exists_run_cases + [
    (["apple", "app", "banana"], "ban", False),
    (["apple", "app", "banana"], "banana", True),
    ([], "anything", False),
]

# ── words_with_prefix ─────────────────────────────────────────────────────────

prefix_run_cases = [
    (["app", "apple", "banana", "band"], "app", {"app", "apple"}),
    (["app", "apple", "banana", "band"], "ban", {"banana", "band"}),
    (["app", "apple", "banana", "band"], "xyz", set()),
]

prefix_submit_cases = prefix_run_cases + [
    (["app", "apple", "banana", "band"], "", {"app", "apple", "banana", "band"}),
    (["app", "apple", "banana", "band"], "apple", {"apple"}),
]

# ── find_matches ──────────────────────────────────────────────────────────────

find_run_cases = [
    (["apple", "banana"], "apple and banana", {"apple", "banana"}),
    (["apple", "banana"], "nothing here", set()),
]

find_submit_cases = find_run_cases + [
    (["app", "apple"], "the apple app", {"app", "apple"}),
    (["hi", "him", "his"], "say hi to him", {"hi", "him"}),
]

# ── advanced_find_matches ─────────────────────────────────────────────────────

adv_run_cases = [
    (["dang", "heck"], "d@ng h3ck", {"@": "a", "3": "e"}, {"d@ng", "h3ck"}),
    (["dang", "heck"], "dang heck", {"@": "a", "3": "e"}, {"dang", "heck"}),
]

adv_submit_cases = adv_run_cases + [
    (["hello", "world"], "h3llo w0rld", {"3": "e", "0": "o"}, {"h3llo", "w0rld"}),
    (["cat"], "c@t", {"@": "a"}, {"c@t"}),
]

# ── longest_common_prefix ─────────────────────────────────────────────────────

lcp_run_cases = [
    (["flower", "flow", "flight"], "fl"),
    (["apple", "application", "apply"], "appl"),
]

lcp_submit_cases = lcp_run_cases + [
    (["interview", "interact", "integrate"], "inte"),
    (["single"], "single"),
]


def build_tree(words):
    t = PrefixTree()
    for w in words:
        t.insert(w)
    return t


def test_exists(words, word, expected):
    t = build_tree(words)
    result = t.exists(word)
    ok = result == expected
    print(f"  exists({word!r}) → {result} {'✓' if ok else '✗ expected ' + str(expected)}")
    return ok


def test_words_with_prefix(words, prefix, expected):
    t = build_tree(words)
    result = set(t.words_with_prefix(prefix))
    ok = result == expected
    print(f"  words_with_prefix({prefix!r}) → {result} {'✓' if ok else '✗ expected ' + str(expected)}")
    return ok


def test_find_matches(words, document, expected):
    t = build_tree(words)
    result = t.find_matches(document)
    ok = result == expected
    print(f"  find_matches({document!r}) → {result} {'✓' if ok else '✗ expected ' + str(expected)}")
    return ok


def test_advanced_find_matches(words, document, variations, expected):
    t = build_tree(words)
    result = t.advanced_find_matches(document, variations)
    ok = result == expected
    print(f"  advanced_find_matches({document!r}, {variations}) → {result} {'✓' if ok else '✗ expected ' + str(expected)}")
    return ok


def test_lcp(words, expected):
    t = build_tree(words)
    result = t.longest_common_prefix()
    ok = result == expected
    print(f"  longest_common_prefix({words}) → {result!r} {'✓' if ok else '✗ expected ' + repr(expected)}")
    return ok


def run_section(name, cases, fn):
    print(f"──── {name} ────────────────────────")
    passed = failed = 0
    for case in cases:
        if fn(*case):
            passed += 1
        else:
            failed += 1
    return passed, failed


def main():
    total_passed = total_failed = 0

    sections = [
        ("exists", exists_cases, test_exists),
        ("words_with_prefix", prefix_cases, test_words_with_prefix),
        ("find_matches", find_cases, test_find_matches),
        ("advanced_find_matches", adv_cases, test_advanced_find_matches),
        ("longest_common_prefix", lcp_cases, test_lcp),
    ]

    for name, cases, fn in sections:
        p, f = run_section(name, cases, fn)
        total_passed += p
        total_failed += f

    if total_failed == 0:
        print("============= PASS ==============")
    else:
        print("============= FAIL ==============")
    print(f"{total_passed} passed, {total_failed} failed")


if "__RUN__" in globals():
    exists_cases = exists_run_cases
    prefix_cases = prefix_run_cases
    find_cases = find_run_cases
    adv_cases = adv_run_cases
    lcp_cases = lcp_run_cases
else:
    exists_cases = exists_submit_cases
    prefix_cases = prefix_submit_cases
    find_cases = find_submit_cases
    adv_cases = adv_submit_cases
    lcp_cases = lcp_submit_cases

main()
