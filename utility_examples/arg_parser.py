import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Async aggregator CLI")
    parser.add_argument(
        "-s", "--sources",
        nargs="+",
        type=str,
        default=["Service_A", "Service_B", "Service_C"],
        metavar="SOURCE",
        help="One or more source IDs to aggregate (default: Service_A Service_B Service_C)",
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=1.0,
        help="Simulated fetch delay in seconds for each source (default: 1.0)",
    )
    return parser.parse_args()
