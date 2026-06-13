# Travelling Salesman Problem (TSP)

The Travelling Salesman Problem is one of the most famous problems in computer science and mathematics. The setup is simple: a salesperson needs to visit a set of cities and return home. What is the shortest route that visits every city exactly once?

This sounds straightforward, but the number of possible routes grows factorially with the number of cities — 10 cities means over 3 million routes, 20 cities means more routes than there are atoms in the observable universe. No known algorithm can guarantee an optimal solution without checking a number of routes that grows this fast.

The version implemented here asks a slightly simpler decision version: **given a set of cities and distances between them, is there a route that visits every city exactly once with total distance ≤ a given bound?**

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
