# Prefix Tree (Trie)

A prefix tree (also called a **trie**, pronounced "try") is a tree-shaped data structure designed for storing and searching strings. Instead of storing each word whole, it breaks words into individual characters and shares common beginnings across words. The words "cat", "car", and "card" all travel the same path c → a → r before branching.

This sharing makes prefix lookups extremely fast: to find all words starting with "car", you simply follow three branches and then collect everything below — no unrelated words are ever visited. Tries are used in autocomplete systems, spell checkers, and anywhere you need to search a large dictionary by prefix.

This implementation adds document scanning and leet-speak matching on top of the basic trie operations.

## How it works

Each node is a plain `dict`. Keys are characters; values are child dicts. The special key `"*"` marks the end of a complete word.

```
insert("cat"), insert("car"), insert("card")

root
└── c
    └── a
        ├── t → {"*": True}
        └── r → {"*": True,
                  d → {"*": True}}
```

To check if a word exists: walk the tree character by character, then check for `"*"` in the final node.

## Operations

| Method | Description | Time |
|---|---|---|
| `insert(word)` | Add a word | O(m) |
| `exists(word)` | Check for exact word | O(m) |
| `words_with_prefix(prefix)` | All words that start with prefix | O(m + k) |
| `find_matches(document)` | All trie words found anywhere in a string | O(d × m) |
| `advanced_find_matches(document, variations)` | Same, but maps substitute characters to their canonical form | O(d × m) |
| `longest_common_prefix()` | Longest prefix shared by all inserted words | O(m) |

*m = word/prefix length, k = number of matches, d = document length*

## Practical example — content moderation

`advanced_find_matches` accepts a `variations` dict so that leet-speak substitutions still match:

```python
tree.insert("hack")
tree.insert("dang")

# {"@": "a", "3": "e", "4": "a"} maps leet chars to canonical
tree.advanced_find_matches("h@ck and d4ng3r", {"@": "a", "3": "e", "4": "a"})
# → {"h@ck", "d4ng"}
```

## Files

| File | Contents |
|---|---|
| `prefix_tree.py` | `PrefixTree` class |
| `test_prefix_tree.py` | Unit tests for all operations |

## Running tests

```bash
python test_prefix_tree.py
```
