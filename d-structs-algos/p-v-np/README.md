# P vs NP

Implementations of two classic NP problems, illustrating the gap between verifying a solution (fast) and finding one (slow).

## The core idea

- **P** — problems solvable in polynomial time (e.g. binary search, sorting)
- **NP** — problems where a *given* solution can be *verified* in polynomial time, but no known polynomial-time algorithm exists to *find* one
- **NP-complete** — the hardest problems in NP; a polynomial algorithm for any one of them would solve all of NP

Both problems here are NP-complete. The brute-force solvers are exponential; the verifiers are polynomial.

## Implementations

| Folder | Problem | Solver complexity | Verifier complexity |
|---|---|---|---|
| [traveling_salesman/](traveling_salesman/) | Travelling Salesman Problem | O(n!) | O(n) |
| [subset_sum/](subset_sum/) | Subset Sum | O(2ⁿ) | O(n) |
