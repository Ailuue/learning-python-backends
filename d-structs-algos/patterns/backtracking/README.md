# Backtracking Problems

**Backtracking** builds a solution one choice at a time, and the moment a
partial choice can't lead anywhere valid, it *undoes* the last choice and tries
the next option. It's depth-first search over the tree of "decisions so far" —
the difference from plain recursion is the explicit **choose → recurse → un-choose**
rhythm that lets one mutable path explore the whole tree without copying it at
every step.

## The signal

The problem asks you to **enumerate or search all combinations/arrangements**:
"all subsets," "all permutations," "every way to sum to a target," "does a path
through this grid spell the word." If the answer is *a count* or *a single best
value* rather than the actual arrangements, DP is often cheaper — backtracking
is for when you genuinely need to walk the possibilities.

The two decisions that define any backtracking problem:

1. **What's a choice?** (which element to add next, which cell to step to)
2. **When do you prune?** A dead branch abandoned early is the whole point — an
   unpruned backtracking search is just brute force with extra steps.

The skeleton, which every problem below is a variation of:

```
def backtrack(path, choices):
    if is_complete(path):
        record(path)              # copy it — path keeps mutating
        return
    for choice in choices:
        if not valid(choice):
            continue              # prune
        path.append(choice)       # choose
        backtrack(path, next_choices(choice))
        path.pop()                # un-choose
```

## The problems ([backtracking_problems.py](backtracking_problems.py))

| Problem | Choice at each step | Pruning / dedup |
|---|---|---|
| `subsets` | include element i, or don't | advance the start index so subsets don't repeat |
| `permutations` | which unused element goes next | a `used` set marks what's taken |
| `combination_sum` | reuse a coin, or move on | stop when the remainder goes negative |
| `word_search` | step to an adjacent grid cell | mark visited, bail on mismatch |

Complexity is inherently exponential (that's the problem space) — pruning is
what keeps it from being *worse* than it has to be.
