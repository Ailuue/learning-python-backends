# ─── 02 · Variables ───────────────────────────────────────────────────────────
#
# Concepts:
#   1. Simple assignment  NAME = value   (recursively expanded — lazy)
#   2. Immediate assignment NAME := value (simply expanded — eager)
#   3. Conditional assignment NAME ?= value (set only if not already defined)
#   4. Append  NAME += value
#   5. Referencing variables: $(NAME) or ${NAME}
#   6. Overriding from the command line: make NAME=value
#   7. Automatic variables: $@ $< $^ $* $(@D) $(@F)
#
# Try:
#   make show            # see how = vs := differ
#   make greet           # see NAME variable in action
#   make greet NAME=Alex # override NAME from the command line
#   make list-files      # see automatic variables in a multi-file rule
#   make env-info        # see shell environment in make
# ─────────────────────────────────────────────────────────────────────────────

.DEFAULT_GOAL := show
.PHONY: show greet list-files env-info append-demo

# ─── CONCEPT 1: Recursively expanded assignment ( = ) ─────────────────────────
#
# The value is NOT evaluated when the variable is defined.
# It's evaluated every time the variable is referenced.
# This means forward references work — but circular references cause infinite loops.
#
# GOTCHA: spaces before a # comment on a variable line become part of the value.
# Always put comments on their own line above the assignment.

# GREETING references NAME before NAME is defined — fine with =, would break with :=
GREETING = Hello, $(NAME)!
NAME     = world

# ─── CONCEPT 2: Simply expanded assignment ( := ) ────────────────────────────
#
# The value IS evaluated immediately when the variable is defined.
# This is the safe default for most variables — no surprises.

TIMESTAMP  := $(shell date '+%H:%M:%S')   # captured once at parse time
TIMESTAMP2  = $(shell date '+%H:%M:%S')   # re-evaluated on every use

# ─── CONCEPT 3: Conditional assignment ( ?= ) ────────────────────────────────
#
# Sets the variable ONLY if it has not already been assigned.
# Useful for providing defaults that callers can override:
#   make greet NAME=Alex      # NAME is already set, ?= does nothing
#   make greet                # NAME is not set, ?= assigns "stranger"

NAME ?= stranger

# ─── CONCEPT 4: Append ( += ) ────────────────────────────────────────────────
#
# Appends to an existing value (adds a space then the new value).

FLAGS  = --verbose
FLAGS += --no-color
# FLAGS is now "--verbose --no-color"

show:
	@echo "=== = vs := comparison ==="
	@echo "GREETING   (=)  : $(GREETING)"
	@echo "TIMESTAMP  (:=) : $(TIMESTAMP)  (captured at parse time)"
	@echo "TIMESTAMP2 (=)  : $(TIMESTAMP2) (re-evaluated now)"
	@echo ""
	@echo "=== Append example ==="
	@echo "FLAGS = $(FLAGS)"

# ─── CONCEPT 6: Command-line override ─────────────────────────────────────────
#
# Any variable can be overridden on the command line:
#   make greet NAME=Alex
#
# Command-line values override both = and := assignments in the Makefile.
# They do NOT override ?= if the variable is set on the CLI before ?= runs.
# (In practice: command-line wins. Use ?= for defaults, = or := for derivations.)

greet:
	@echo "$(GREETING)"
	@echo "(Change NAME with: make greet NAME=YourName)"

# ─── CONCEPT 7: Automatic variables ──────────────────────────────────────────
#
# Inside a recipe, make provides special variables for the current rule:
#
#   $@   — the TARGET name
#   $<   — the FIRST prerequisite
#   $^   — ALL prerequisites (space-separated, no duplicates)
#   $?   — prerequisites NEWER than the target
#   $*   — the stem matched by a pattern rule (see 03_dependencies)
#
# Directory and file components:
#   $(@D) — directory part of $@    (e.g. "src")
#   $(@F) — filename part of $@     (e.g. "main.py")

output/report.txt: data/a.txt data/b.txt
	@echo "Target       : $@"
	@echo "First prereq : $<"
	@echo "All prereqs  : $^"
	@mkdir -p $(@D)
	@echo "Generated from $^" > $@
	@echo "Created $@"

list-files: output/report.txt
	@echo ""
	@echo "Contents of $<:"
	@cat $<

# ─── CONCEPT: Environment variables ──────────────────────────────────────────
#
# Shell environment variables are imported into make variables automatically.
# But make variables do NOT flow back to the shell environment of other recipes
# unless you use export.

export EXPORTED_VAR = I am visible to child processes

env-info:
	@echo "HOME from env   : $(HOME)"
	@echo "EXPORTED_VAR    : $(EXPORTED_VAR)"
	@echo "Verify in shell : $$EXPORTED_VAR"

# ─── Housekeeping ─────────────────────────────────────────────────────────────

clean:
	rm -rf output/

append-demo:
	@echo "FLAGS before append: --verbose"
	@echo "FLAGS after += :     $(FLAGS)"
