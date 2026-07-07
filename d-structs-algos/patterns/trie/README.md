# Trie (Word) Problems

A **trie** (prefix tree) stores a set of strings as a tree of characters, so
that every shared prefix is stored once. This repo already builds one from
scratch in [../../prefix_tree/](../../prefix_tree/) — that folder is the *data
structure*; this one is the *interview pattern*: the questions where reaching for
a trie turns an O(words × length) scan into a single walk down shared prefixes.

## The signal

The problem is about **prefixes or a dictionary of words** and you'd otherwise
compare a query against every stored word: "autocomplete / words with this
prefix," "search a word with `.` wildcards," "replace each word by its shortest
dictionary root," "does this board contain any of these 10,000 words." The trie
pays off precisely when many words **share prefixes** — it collapses that shared
work.

Two capabilities beyond a plain hash set, which is why a set isn't enough:

- **Prefix queries.** A set answers "is this exact word present?"; a trie also
  answers "is this a prefix of anything?" and "give me everything under it."
- **Character-by-character search**, which is what makes **wildcards** (`.`
  matches any letter) and **grid word-search** tractable — you advance one
  character at a time and prune the instant no branch matches.

The interview-favorite combination: **Trie + backtracking on a grid** (Word
Search II). Building one trie from the whole word list lets a single DFS over the
board find *all* the words at once, pruning any path whose prefix isn't in the
trie — vastly better than running the single-word search once per word.

## The pieces ([trie_problems.py](trie_problems.py))

| Piece | What it adds over a hash set |
|---|---|
| `Trie` | `insert`, `search`, `starts_with` — the baseline (LeetCode 208) |
| `WordDictionary` | `search` supports `.` wildcards (branches at each dot) |
| `replace_words` | replace each word by the shortest dictionary root that prefixes it |
| `find_words_on_board` | Trie + grid backtracking: find every dictionary word in a board |

Complexity is measured in **total characters**, not word count — insert/search a
word of length L is O(L) regardless of how many words are stored.
