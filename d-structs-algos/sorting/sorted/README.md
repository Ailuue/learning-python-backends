# Python's `sorted()` with a Custom Key

In real code, you rarely need to implement your own sorting algorithm. Python's built-in `sorted()` function is fast, stable, and covers the vast majority of sorting needs. The key skill is knowing how to tell it **what to sort by** when you're working with custom objects or non-obvious orderings.

This is done with the `key=` argument: you provide a function that extracts a comparable value from each element, and `sorted()` uses those values to determine order. This pattern is used constantly — sorting users by signup date, sorting search results by relevance score, sorting products by price.

## The problem

How do you sort a list of `Influencer` objects by their "vanity score" — a formula combining two attributes?

```python
class Influencer:
    num_selfies: int
    num_bio_links: int
```

## The solution — `key=`

Define a function that maps each object to a comparable value, then pass it as `key`:

```python
def vanity(influencer: Influencer) -> int:
    return influencer.num_bio_links * 5 + influencer.num_selfies

sorted(influencers, key=vanity)
```

`sorted()` calls `vanity(obj)` for each element and sorts by the returned integers. The original objects are returned in sorted order — `vanity` is only used for comparison.

## Why this matters

- Avoids implementing a full sort algorithm for every custom ordering
- `key=` is called exactly once per element (not once per comparison), so it's efficient
- Works with `sort()` (in-place) and `sorted()` (new list) alike
- Python's sort is **stable** — objects with equal vanity scores keep their original relative order

## Files

| File | Contents |
|---|---|
| `sorting.py` | `Influencer` class, `vanity` key, `vanity_sort` function |
| `test_sorting.py` | Unit tests |

## Running tests

```bash
python test_sorting.py
```
