"""
Order Processing Worker
========================
Consumes events from the "order.placed" topic and processes them.
Runs as a separate process alongside the FastAPI app.

This worker belongs to the "order-processor" consumer group. You can run
multiple copies of it — Kafka will distribute partitions between them
automatically, scaling throughput linearly.

    python worker.py           # instance 1
    python worker.py           # instance 2 (in a separate terminal)
    → Kafka splits partitions between them; no duplicate processing

At-least-once delivery
    This worker uses manual commits: it only commits the offset after
    successfully processing a message. If the worker crashes mid-processing,
    the message is re-delivered on restart.

    Implication: your processing logic should be idempotent — processing
    the same order twice should not double-charge the customer.
    Common approach: check if order_id already exists in the DB before acting.

Run:
    python worker.py
    (Keep this running while you POST to the FastAPI app.)
"""

import json
import signal
import sys
import time

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

BOOTSTRAP = "localhost:9092"
TOPIC = "order.placed"
GROUP_ID = "order-processor"

running = True


def handle_signal(sig, frame):
    global running
    print("\nShutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


# ---------------------------------------------------------------------------
# Simulated processing steps
# ---------------------------------------------------------------------------

def validate_order(event: dict) -> bool:
    return event.get("quantity", 0) > 0 and bool(event.get("item"))


def charge_payment(event: dict) -> bool:
    time.sleep(0.05)   # simulate payment API call
    return True


def send_confirmation(event: dict) -> None:
    time.sleep(0.02)   # simulate email service call
    pass


def process_order(event: dict) -> None:
    order_id = event["order_id"]
    customer = event["customer_id"]

    print(f"\n  ┌── Processing order {order_id} for {customer}")
    print(f"  │   item={event['item']}  qty={event['quantity']}")

    if not validate_order(event):
        print("  └── REJECTED: invalid order data")
        return

    print("  │   [1/3] validated ✓")

    if not charge_payment(event):
        print("  └── FAILED: payment declined")
        return

    print("  │   [2/3] payment charged ✓")

    send_confirmation(event)
    print("  │   [3/3] confirmation sent ✓")
    print(f"  └── DONE  (latency: {(time.time() - event['created_at']) * 1000:.0f}ms from event creation)")


# ---------------------------------------------------------------------------
# Main consumer loop
# ---------------------------------------------------------------------------

def main():
    print("=== Order Worker ===")
    print(f"    topic={TOPIC}  group={GROUP_ID}")
    print("    Waiting for events... (Ctrl-C to stop)\n")

    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=BOOTSTRAP,
            group_id=GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=False,   # manual commit after processing
            value_deserializer=lambda v: json.loads(v.decode()),
            key_deserializer=lambda k: k.decode() if k else None,
        )
    except NoBrokersAvailable:
        print("ERROR: Kafka not reachable. Run:  docker compose up -d")
        sys.exit(1)

    while running:
        records = consumer.poll(timeout_ms=500)   # non-blocking poll
        for partition_records in records.values():
            for message in partition_records:
                try:
                    process_order(message.value)
                    consumer.commit()   # advance offset only on success
                except Exception as e:
                    # In production: send to a dead-letter topic instead of skipping.
                    print(f"  ERROR processing message: {e}  (skipping)")
                    consumer.commit()

    consumer.close()
    print("Worker stopped.")


if __name__ == "__main__":
    main()
