# ─── 04 · Functions ───────────────────────────────────────────────────────────
#
# Concepts:
#   1. $(wildcard pattern)         — glob expansion at parse time
#   2. $(patsubst from,to,list)    — pattern substitution on a list
#   3. $(subst from,to,text)       — simple string substitution
#   4. $(filter pattern,list)      — keep items matching a pattern
#   5. $(filter-out pattern,list)  — remove items matching a pattern
#   6. $(sort list)                — sort and deduplicate
#   7. $(dir names)                — extract directory part of paths
#   8. $(notdir names)             — extract filename part of paths
#   9. $(basename names)           — strip final extension
#  10. $(suffix names)             — extract the extension
#  11. $(foreach var,list,body)    — loop over a list
#  12. $(shell command)            — run a shell command, capture stdout
#  13. $(info message)             — print a message during parsing
#  14. $(warning message)          — print a warning (doesn't abort)
#  15. $(error message)            — abort with an error message
#  16. $(if condition,then,else)   — inline conditional
#  17. $(call variable,args)       — call a user-defined macro
#
# Try:
#   make show-string-ops    # concepts 1-10
#   make show-loop          # concept 11 — foreach
#   make show-shell         # concept 12 — shell
#   make show-control       # concepts 13-16
#   make show-call          # concept 17 — user-defined macro
# ─────────────────────────────────────────────────────────────────────────────

.DEFAULT_GOAL := show-all
.PHONY: show-all show-string-ops show-loop show-shell show-control show-call clean

# ─── Setup: some lists to work with ───────────────────────────────────────────

WORDS    = alpha beta gamma delta alpha beta
PATHS    = src/main.py src/utils.py tests/test_main.py tests/test_utils.py
SOURCES  = $(filter src/%.py,   $(PATHS))   # CONCEPT 4: only src/ files
TESTS    = $(filter tests/%.py, $(PATHS))   # CONCEPT 4: only tests/ files

# ─── CONCEPT 1–10: String operations ──────────────────────────────────────────

show-string-ops:
	@echo "=== 1. wildcard ==="
	@echo "  PY files in this dir  : $(wildcard *.py)"
	@echo "  MK files in this dir  : $(wildcard *.mk Makefile)"

	@echo ""
	@echo "=== 2. patsubst ==="
	@echo "  PATHS                 : $(PATHS)"
	@echo "  .py → .pyc            : $(patsubst %.py,%.pyc,$(PATHS))"

	@echo ""
	@echo "=== 3. subst ==="
	@echo "  'src/' → 'lib/'       : $(subst src/,lib/,$(PATHS))"

	@echo ""
	@echo "=== 4–5. filter and filter-out ==="
	@echo "  SOURCES (src/ only)   : $(SOURCES)"
	@echo "  TESTS   (tests/ only) : $(TESTS)"
	@echo "  Non-test files        : $(filter-out tests/%,$(PATHS))"

	@echo ""
	@echo "=== 6. sort ==="
	@echo "  Original WORDS        : $(WORDS)"
	@echo "  Sorted + deduped      : $(sort $(WORDS))"

	@echo ""
	@echo "=== 7–10. Path component functions ==="
	@echo "  Paths                 : $(PATHS)"
	@echo "  dir   (directory)     : $(dir $(PATHS))"
	@echo "  notdir (filename)     : $(notdir $(PATHS))"
	@echo "  basename (no ext)     : $(basename $(PATHS))"
	@echo "  suffix (extension)    : $(suffix $(PATHS))"

# ─── CONCEPT 11: foreach ──────────────────────────────────────────────────────
#
# $(foreach var,list,body) iterates over space-separated words in list.
# var takes each value in turn; body is expanded for each.
# Results are concatenated with spaces.

SERVICES = api worker beat

show-loop:
	@echo "=== foreach: generate docker stop commands ==="
	@echo "$(foreach svc,$(SERVICES),docker stop $(svc))"
	@echo ""
	@echo "=== foreach: uppercase-ish label ==="
	@echo "$(foreach svc,$(SERVICES),  [$(svc)])"
	@echo ""
	@echo "=== foreach in a recipe (one line per iteration) ==="
	@$(foreach svc,$(SERVICES), echo "  checking: $(svc)";)

# ─── CONCEPT 12: shell ────────────────────────────────────────────────────────
#
# $(shell command) runs a shell command at parse time and returns its stdout.
# Use := so it only runs once, not every time the variable is referenced.

GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "not-a-repo")
PY_VERSION := $(shell python3 --version 2>&1 | cut -d' ' -f2)
TODAY      := $(shell date '+%Y-%m-%d')

show-shell:
	@echo "=== shell: capture command output ==="
	@echo "  Git branch     : $(GIT_BRANCH)"
	@echo "  Python version : $(PY_VERSION)"
	@echo "  Today          : $(TODAY)"
	@echo ""
	@echo "=== inline shell in a recipe ==="
	@echo "  Files here     : $$(ls | head -5 | tr '\n' ' ')"

# ─── CONCEPTS 13–16: info, warning, error, if ────────────────────────────────
#
# info and warning print during parsing — before any recipes run.
# error aborts make entirely.
# if is an inline conditional: $(if condition,then-value,else-value)
#   condition is true if it's a non-empty string.

$(info  [info] Makefile loaded. Run 'make show-control' to see more.)

show-control:
	@echo "=== $(if $(GIT_BRANCH),Git branch: $(GIT_BRANCH),Not in a git repo) ==="
	@echo ""
	@echo "=== warning prints during parsing, not here ==="
	@echo "=== error aborts make — not demonstrated here (would stop the build) ==="
	@echo ""
	@echo "Inline if examples:"
	@echo "  GIT_BRANCH set?  : $(if $(GIT_BRANCH),yes,no)"
	@echo "  UNSET_VAR set?   : $(if $(UNSET_VAR),yes,no)"

# ─── CONCEPT 17: call (user-defined macro) ────────────────────────────────────
#
# $(call macro,arg1,arg2,...) lets you define parameterized text templates.
# Inside the macro, $1 $2 ... refer to the arguments.

docker-run = docker run --rm -e ENV=$(1) $(2) $(if $(3),$(3),/bin/sh)

show-call:
	@echo "=== call: expand a parameterized macro ==="
	@echo "  Template  : docker run --rm -e ENV=<env> <image> [cmd]"
	@echo ""
	@echo "  $(call docker-run,staging,python:3.13)"
	@echo "  $(call docker-run,production,python:3.13,python manage.py migrate)"

# ─── Convenience targets ──────────────────────────────────────────────────────

show-all: show-string-ops show-loop show-shell show-control show-call

clean:
	@echo "(nothing to clean in this section)"
