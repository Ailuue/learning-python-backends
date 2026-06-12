# Travelling Salesman Problem (TSP)

Given a set of cities and distances between them, is there a route that visits every city exactly once with total distance ≤ a given bound?

## Why it's hard

There are **n!** possible orderings of n cities. For 10 cities that's 3,628,800 routes. For 20 cities it's 2.4 × 10¹⁸ — infeasible to check exhaustively.

## Implementation

The solver generates all permutations of the city list using **Heap's algorithm** (an efficient permutation generator), then checks the total distance of each route:

```python
tsp(cities=[0, 1, 2], paths=distances, dist=10)
# Returns True if any Hamiltonian path has total distance ≤ 10
```

The verifier checks a single given route in O(n):

```python
verify_tsp(paths=distances, dist=10, actual_path=[0, 2, 1])
# Returns True if this specific path has total distance ≤ 10
```

## The P vs NP illustration

- `tsp()` — O(n!) to find a valid route
- `verify_tsp()` — O(n) to confirm one

If someone hands you a route and claims it works, you can check it instantly. But finding that route yourself requires trying (essentially) all possibilities.

## Complexity

| Function | Time |
|---|---|
| `tsp` (solver) | O(n!) |
| `verify_tsp` (verifier) | O(n) |

## Files

| File | Contents |
|---|---|
| `traveling_salesman.py` | `tsp`, `verify_tsp`, `permutations` (Heap's algorithm) |
| `test_traveling_salesman.py` | Unit tests |

## Running tests

```bash
python test_traveling_salesman.py
```
