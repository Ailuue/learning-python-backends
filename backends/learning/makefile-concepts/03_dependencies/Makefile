# ─── 03 · Dependencies ────────────────────────────────────────────────────────
#
# Concepts:
#   1. File-based dependencies — make checks timestamps
#   2. Target dependency chains — how the build DAG works
#   3. Pattern rules — %.txt: %.md handles every file with one rule
#   4. Automatic variable $* — the matched stem in a pattern rule
#   5. Incremental rebuilds — make skips up-to-date targets
#   6. Forcing rebuilds with -B and touch
#
# Setup: source files are in src/  (chapter1.md, chapter2.md, chapter3.md)
#        this Makefile "processes" them into build/  (*.txt files)
#        then assembles them into build/book.txt
#
# Try:
#   make              # builds everything
#   make              # again — nothing happens ("Nothing to be done")
#   touch src/chapter1.md && make   # only chapter1 rebuilds
#   make -B           # force-rebuild everything regardless of timestamps
#   make build/chapter2.txt        # build a specific output file
# ─────────────────────────────────────────────────────────────────────────────

.DEFAULT_GOAL := all
.PHONY: all clean show-dag

BUILD_DIR = build
SRC_DIR   = src

# ─── CONCEPT 1: Listing sources and deriving outputs ──────────────────────────
#
# $(wildcard ...) — expand a glob pattern at parse time.
# $(patsubst from,to,list) — transform a list of strings.
#
# These two lines say:
#   SOURCES = src/chapter1.md src/chapter2.md src/chapter3.md
#   OUTPUTS = build/chapter1.txt build/chapter2.txt build/chapter3.txt
#
SOURCES = $(wildcard $(SRC_DIR)/*.md)
OUTPUTS = $(patsubst $(SRC_DIR)/%.md, $(BUILD_DIR)/%.txt, $(SOURCES))

# ─── CONCEPT 2: Top-level phony target depends on all output files ─────────────
#
# `all` depends on OUTPUTS (the .txt files) AND build/book.txt.
# Make resolves the full dependency graph before running any recipe.

all: $(BUILD_DIR)/book.txt

# ─── CONCEPT 3: Pattern rule ──────────────────────────────────────────────────
#
# A single rule that handles EVERY file matching the pattern.
#
#   %.txt: %.md    "any .txt target in build/ depends on the matching .md in src/"
#
# % is a wildcard stem. For build/chapter1.txt it matches "chapter1".
#
# $*  — the stem (e.g. "chapter1")
# $@  — the full target path (e.g. "build/chapter1.txt")
# $<  — the first prerequisite (e.g. "src/chapter1.md")

$(BUILD_DIR)/%.txt: $(SRC_DIR)/%.md
	@mkdir -p $(BUILD_DIR)
	@echo "[process] $< → $@"
	@echo "=== $* ===" > $@
	@cat $< >> $@

# ─── CONCEPT 4: A target that depends on other targets (the DAG) ──────────────
#
# book.txt depends on ALL the chapter .txt files.
# Make runs each chapter's recipe first (if needed), then runs this one.
#
# Dependency graph:
#
#   all
#    └── build/book.txt
#         ├── build/chapter1.txt  ← depends on src/chapter1.md
#         ├── build/chapter2.txt  ← depends on src/chapter2.md
#         └── build/chapter3.txt  ← depends on src/chapter3.md

$(BUILD_DIR)/book.txt: $(OUTPUTS)
	@echo "[assemble] combining chapters → $@"
	@cat $(OUTPUTS) > $@
	@echo "[done] $@ is ready."
	@echo ""
	@echo "Contents:"
	@cat $@

# ─── CONCEPT 5: Incremental rebuilds ─────────────────────────────────────────
#
# Make compares modification timestamps:
#   - If build/chapter1.txt is NEWER than src/chapter1.md → skip
#   - If src/chapter1.md was changed AFTER build/chapter1.txt → rebuild
#
# Demonstrate this:
#   1. Run `make`      → builds everything
#   2. Run `make`      → "Nothing to be done for 'all'."
#   3. Run `touch src/chapter2.md && make`
#      → only build/chapter2.txt and build/book.txt rebuild (their deps changed)
#   4. Run `make -B`   → rebuild everything regardless of timestamps

show-dag:
	@echo "Sources  : $(SOURCES)"
	@echo "Outputs  : $(OUTPUTS)"
	@echo ""
	@echo "Dependency graph:"
	@echo "  all → build/book.txt → [$(notdir $(OUTPUTS))]"

clean:
	rm -rf $(BUILD_DIR)
