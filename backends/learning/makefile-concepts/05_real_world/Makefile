# ─── 05 · Real-World Patterns ─────────────────────────────────────────────────
#
# Concepts:
#   1. Self-documenting help target  — ## comment convention
#   2. define / endef               — multi-line variable (macro block)
#   3. ifeq / ifneq / ifdef         — conditionals at parse time
#   4. include                      — split large Makefiles across files
#   5. Color output with ANSI codes
#   6. Guard targets                — prerequisites that abort on bad state
#   7. Confirmation prompt          — asking "are you sure?"
#   8. Putting it all together      — a realistic project Makefile
#
# Try:
#   make             # prints the help menu
#   make show-define # multi-line macro example
#   make show-cond   # conditionals demo
#   make greet       # uses ENV conditional
#   make ENV=production greet
# ─────────────────────────────────────────────────────────────────────────────

# ─── CONCEPT 1: Self-documenting help ─────────────────────────────────────────
#
# Convention: add a ## comment after any target you want to appear in help.
# The help recipe greps for the pattern and formats an aligned table.
# Targets WITHOUT ## are intentionally hidden from the menu.
#
# This pattern is ubiquitous in real project Makefiles. Users can discover
# available commands with a single `make` or `make help`.

.DEFAULT_GOAL := help

help: ## Show this help message
	@echo ""
	@echo "Usage: make <target> [VAR=value]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	| sort \
	| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-18s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ─── CONCEPT 5: Color output ──────────────────────────────────────────────────
#
# ANSI escape codes. Using := so they expand once.
# Conditional: if NO_COLOR is set (a common convention), disable colors.

ifdef NO_COLOR
  CYAN  :=
  GREEN :=
  RESET :=
else
  CYAN  := \033[36m
  GREEN := \033[32m
  RESET := \033[0m
endif

# ─── CONCEPT 3: Conditionals ──────────────────────────────────────────────────
#
# ifeq / ifneq / ifdef / ifndef evaluate at PARSE time, not recipe time.
# They are make-level conditionals — not shell if statements.
#
#   ifeq ($(VAR), value)   — if VAR equals "value"
#   ifneq                  — if VAR does not equal "value"
#   ifdef VAR              — if VAR is defined (even if empty)
#   ifndef VAR             — if VAR is not defined
#
# Common use: choose behavior based on an ENV variable:

ENV ?= development

ifeq ($(ENV), production)
  LOG_LEVEL = error
  DEBUG     = false
else ifeq ($(ENV), staging)
  LOG_LEVEL = warning
  DEBUG     = false
else
  LOG_LEVEL = debug
  DEBUG     = true
endif

show-cond: ## Show how conditionals select different values
	@echo "ENV       = $(ENV)"
	@echo "LOG_LEVEL = $(LOG_LEVEL)"
	@echo "DEBUG     = $(DEBUG)"
	@echo ""
	@echo "Try: make show-cond ENV=staging"
	@echo "     make show-cond ENV=production"

greet: ## Print a greeting that varies by ENV
	@echo "$(GREEN)[$(ENV)]$(RESET) Hello — log level is $(LOG_LEVEL)"

# ─── CONCEPT 2: define / endef ────────────────────────────────────────────────
#
# define creates a multi-line variable. Useful for:
#   - Multi-line shell scripts that would be messy with backslash continuation
#   - Reusable command blocks (call with $(eval $(call macro,...)))
#
# Inside a define block, $(1) $(2) etc. are macro arguments (via $(call)).

define BANNER
@echo ""
@echo "  ╔═════════════════════════╗"
@echo "  ║  $(1)"
@echo "  ╚═════════════════════════╝"
@echo ""
endef

show-define: ## Show multi-line define / endef macro
	$(call BANNER,Multi-line macro block)
	@echo "  define blocks keep multi-line scripts readable."
	@echo "  Call them with \$$(call MACRO_NAME,arg1,arg2)"
	$(call BANNER,Done)

# ─── CONCEPT 6: Guard targets ─────────────────────────────────────────────────
#
# A guard is a phony target that checks a precondition and aborts if it fails.
# Other targets list the guard as a prerequisite.
#
# Example: require that docker is running before `make up`.

check-docker: ## (guard) Verify Docker is running
	@docker info > /dev/null 2>&1 || \
	  (echo "$(CYAN)Error:$(RESET) Docker is not running. Start Docker and retry." && exit 1)
	@echo "$(GREEN)✓$(RESET) Docker is running."

check-env-file: ## (guard) Verify .env file exists
	@test -f .env || \
	  (echo "$(CYAN)Error:$(RESET) .env not found. Copy .env.example and fill in values." && exit 1)
	@echo "$(GREEN)✓$(RESET) .env found."

# Usage: make up depends on the guard
# up: check-docker check-env-file ## Start all services

# ─── CONCEPT 7: Confirmation prompt ───────────────────────────────────────────
#
# For destructive targets (reset DB, tear down prod), ask the operator to type
# "yes" before proceeding. The shell `read` command captures input.
#
# Note: this only works in interactive terminals, not in CI.
# Guard CI usage with:  ifndef CI ... prompt ... endif

confirm-reset: ## (demo) Prompt before a destructive action
	@echo "This will drop and recreate the database."
	@read -p "Type 'yes' to continue: " ans && [ "$${ans}" = "yes" ] || \
	  (echo "Aborted." && exit 1)
	@echo "$(GREEN)Proceeding...$(RESET)"

# ─── CONCEPT 4: include ────────────────────────────────────────────────────────
#
# include reads another Makefile into the current one at parse time.
# Useful for splitting a large Makefile by concern:
#
#   include make/docker.mk
#   include make/db.mk
#   include make/test.mk
#
# If the file doesn't exist, make aborts. Use -include to silently skip it:
#
#   -include .env.mk    # optional local overrides
#
# Demonstrated but not activated here (would need the .mk files to exist):
include-demo: ## (demo) Show what include looks like in practice
	@echo "In a real project Makefile:"
	@echo ""
	@echo "  include make/docker.mk    # adds up, down, logs targets"
	@echo "  include make/db.mk        # adds migrate, seed, db-shell"
	@echo "  include make/test.mk      # adds test, test-cov"
	@echo "  -include .local.mk        # optional local developer overrides"
	@echo ""
	@echo "Each .mk file is a normal Makefile fragment."
	@echo "All targets and variables are merged into one namespace."

# ─── All together: what a realistic project Makefile looks like ───────────────

summary: ## Print a summary of all real-world patterns shown here
	$(call BANNER,Real-World Makefile Patterns)
	@echo "  1. help target    — \$$(make) shows a menu automatically"
	@echo "  2. define/endef   — multi-line macros for clean recipes"
	@echo "  3. ifeq/ifneq     — parse-time conditionals for ENV variants"
	@echo "  4. include        — split large Makefiles into .mk fragments"
	@echo "  5. Color output   — ANSI codes + NO_COLOR convention"
	@echo "  6. Guard targets  — prerequisites that abort on bad state"
	@echo "  7. Confirm prompt — 'type yes to continue' for destructive ops"
	@echo ""

.PHONY: help show-cond greet show-define check-docker check-env-file \
        confirm-reset include-demo summary
