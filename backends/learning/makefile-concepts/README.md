# Makefile Concepts

> 📚 [Backend Learning](../README.md) · **Specialized topic** — best after the core path.

Practical Makefile examples you can run and poke at. Each section is a
standalone directory — `cd` in and run `make` or `make help`.

## Sections

| # | Folder | Concepts covered |
|---|--------|-----------------|
| 1 | `01_basics/` | Default target, `.PHONY`, tab requirement, `@` prefix, dry run |
| 2 | `02_variables/` | `=` vs `:=` vs `?=` vs `+=`, automatic variables, CLI override |
| 3 | `03_dependencies/` | File-based deps, target chains, DAG, incremental rebuilds |
| 4 | `04_functions/` | `wildcard`, `patsubst`, `filter`, `shell`, `info`, `error`, `foreach` |
| 5 | `05_real_world/` | Self-documenting `help`, `define`, conditionals, the full project pattern |

## How to run a section

```bash
cd 01_basics
make          # runs the default target
make help     # where available — shows available targets
make -n       # dry-run: print commands without executing
```

## Why Makefiles?

Make predates Docker, CI, and build tools by decades — but its model
(targets → dependencies → recipes) maps directly onto every build and
dev-workflow problem you'll encounter:

- Build: compile only changed files
- Dev: `make run`, `make test`, `make migrate` with one command
- CI: `make lint && make test` — same locally and in the pipeline
- Docs: `make help` gives new teammates a menu of available actions

The goal here is to understand the mechanics well enough to write and
read project Makefiles confidently, not to become a Make expert.
