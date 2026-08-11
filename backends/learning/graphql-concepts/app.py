"""
GraphQL Playground Server
==========================

Mounts each section's schema at its own URL so you can explore them
interactively in the browser using the built-in GraphiQL playground.

Run:
    pip install -r requirements.txt
    uvicorn app:app --reload

Then open:
    http://localhost:8000/          ← index listing all sections
    http://localhost:8000/01/       ← section 01 playground
    http://localhost:8000/02/       ← section 02 playground
    ... etc.
"""

import importlib.util
import sys
from pathlib import Path

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter

app = FastAPI(title="GraphQL Practice")

ROOT = Path(__file__).parent

SECTIONS = [
    ("01_schema_basics", "Schema Basics — types, queries, mutations"),
    ("02_relationships", "Relationships & N+1 — resolver methods, N+1 problem"),
    ("03_dataloaders",   "DataLoaders — batching to solve N+1"),
    ("04_types",         "Types — enums, unions, interfaces, custom scalars"),
    ("05_mutations",     "Mutations — CRUD and typed error handling"),
    ("06_pagination",    "Pagination — offset and cursor (Relay) patterns"),
]


def load_schema(section_dir: str):
    """Import schema.py from a numbered section directory."""
    path = ROOT / section_dir / "schema.py"
    spec = importlib.util.spec_from_file_location(f"{section_dir}.schema", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load a schema module from {path}")
    mod = importlib.util.module_from_spec(spec)
    # Each section needs its own sys.path entry for relative imports
    section_path = str(ROOT / section_dir)
    sys.path.insert(0, section_path)
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod


for section_dir, title in SECTIONS:
    try:
        mod = load_schema(section_dir)

        # Section 03 needs a context_getter for its DataLoader
        if section_dir == "03_dataloaders":
            router = GraphQLRouter(
                mod.schema,
                context_getter=mod.make_context,
            )
        else:
            router = GraphQLRouter(mod.schema)

        prefix = f"/{section_dir[:2]}"   # /01, /02, ...
        app.include_router(router, prefix=prefix)
    except Exception as exc:
        print(f"[warn] Could not load {section_dir}: {exc}")


@app.get("/")
def index():
    return {
        "sections": [
            {
                "path": f"/{d[:2]}/graphql",
                "title": title,
                "playground": f"http://localhost:8000/{d[:2]}/graphql",
            }
            for d, title in SECTIONS
        ]
    }
