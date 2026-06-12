# Utility Examples

Small standalone scripts demonstrating Python standard library and common utility patterns.

## Files

| File | What it demonstrates |
|---|---|
| `arg_parser.py` | `argparse` — building a CLI with flags, defaults, and type coercion |
| `async_aggregator.py` | `asyncio` — fetching from multiple sources concurrently and aggregating results |
| `data_pipeline.py` | ETL pattern — extract from an HTTP API, transform with pandas, load to output |

## Running

Each file is self-contained:

```bash
python arg_parser.py --help
python async_aggregator.py
python data_pipeline.py
```

`data_pipeline.py` requires `pandas` and `requests`:
```bash
pip install pandas requests
```
