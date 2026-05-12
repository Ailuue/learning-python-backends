import asyncio
import time
from arg_parser import parse_args


async def fetch_data(source_id: str, delay: float) -> dict:
    """Simulates an async API call to a specific data source."""
    print(f"[Source {source_id}] Starting fetch...")
    await asyncio.sleep(delay)
    return {"source": source_id, "data": f"Result from {source_id}"}


async def async_aggregator(sources: list) -> dict:
    """
    Collects multiple async tasks and aggregates them into one result.
    """
    print("Aggregator: Launching all requests concurrently...\n")

    # Create tasks for all sources
    tasks = [fetch_data(s["id"], s["delay"]) for s in sources]

    # asyncio.gather runs them in parallel and waits for all to finish
    results = await asyncio.gather(*tasks)

    # Aggregate logic: combine individual results into a single object
    return {
        "summary": f"Aggregated {len(results)} sources",
        "details": results,
        "timestamp": time.strftime("%H:%M:%S"),
    }


async def main() -> None:
    args = parse_args()
    sources = [{"id": source_id, "delay": args.delay} for source_id in args.sources]

    start = time.perf_counter()
    report = await async_aggregator(sources)
    end = time.perf_counter()

    print(f"\nFinal Report: {report['summary']}")
    for item in report["details"]:
        print(f" - {item['data']}")
    print(f"\nTotal Time: {end - start:.2f} seconds")


# Example CLI usage: python async_aggregator.py -s Service_A Service_B -d 2.0
if __name__ == "__main__":
    asyncio.run(main())
