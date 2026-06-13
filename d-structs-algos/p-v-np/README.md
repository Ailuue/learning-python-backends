# P vs NP

Some problems are easy for a computer to solve. Others seem fundamentally hard — not because we haven't found a clever enough algorithm yet, but because the problems themselves may require exploring an astronomically large space of possibilities. P vs NP is the central open question in computer science about whether those two categories are actually different.

## The core idea

- **P** — problems a computer can *solve* quickly (in polynomial time, e.g. O(n), O(n²)). Examples: binary search, sorting, shortest path.
- **NP** — problems where a *given* solution can be *verified* quickly, but where no one knows how to *find* one quickly. If someone hands you a candidate answer, you can check it in polynomial time — but discovering that answer yourself seems to require trying vast numbers of possibilities.
- **NP-complete** — the hardest problems in NP. If you could solve any one NP-complete problem quickly, you could solve *all* NP problems quickly. Most computer scientists believe P ≠ NP (i.e., these hard problems are genuinely hard), but this has never been proven.

The practical takeaway: for NP-complete problems, there is no known algorithm that scales well. Real-world solutions rely on approximations, heuristics, or constraints that make specific instances tractable.

Both problems here are NP-complete. The brute-force solvers are exponential; the verifiers are polynomial.

## Implementations

| Folder | Problem | Solver complexity | Verifier complexity |
|---|---|---|---|
| [traveling_salesman/](traveling_salesman/) | Travelling Salesman Problem | O(n!) | O(n) |
| [subset_sum/](subset_sum/) | Subset Sum | O(2ⁿ) | O(n) |
