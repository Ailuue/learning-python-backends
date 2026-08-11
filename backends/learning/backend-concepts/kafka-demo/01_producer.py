"""
Kafka Producer
===============
A producer publishes messages to a named topic. Kafka appends each message
to the end of a log file on disk — it doesn't remove messages once they're
consumed (unlike a traditional queue). Consumers track where they are in
the log using an offset.

    Producer ──▶ Topic: orders
                 ┌────────────────────────────────────────────────┐
    Partition 0  │ msg0 │ msg1 │ msg2 │ msg3 │ msg4 │ ...        │
                 └────────────────────────────────────────────────┘
                   ↑ offset 0         ↑ offset 4

Key producer concepts
    send(topic, value, key)
        Non-blocking. Returns a Future. The message is buffered locally and
        sent in batches to the broker for throughput.

    flush()
        Blocks until all buffered messages are acknowledged by the broker.
        Call before exiting or before a critical checkpoint.

    Serialisation
        Kafka messages are raw bytes. You define how to encode/decode.
        JSON is fine for learning; Avro or Protobuf are used in production
        for schema enforcement and smaller payloads.

    acks
        acks=0  → fire-and-forget, fastest, can lose messages
        acks=1  → broker leader acknowledges, default
        acks=-1 → all in-sync replicas acknowledge, safest (use with retries)

Prerequisites:
    docker compose up -d
    (wait ~10s for Kafka to start)

Run:
    python 01_producer.py
"""

import json
import time

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

BOOTSTRAP = "localhost:9092"
TOPIC = "orders"


def make_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
        # A None key is meaningful to Kafka (no key -> round-robin partitioning),
        # but typeshed's kafka-python stub types the serializer as returning bytes.
        # pyright: ignore is the right call here — b"" would change partitioning.
        key_serializer=lambda k: str(k).encode() if k else None,  # pyright: ignore[reportArgumentType]
        acks="all",       # wait for all in-sync replicas
        retries=3,
    )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=== Kafka Producer Demo ===\n")

    try:
        producer = make_producer()
    except NoBrokersAvailable:
        print("ERROR: Kafka not reachable. Run:  docker compose up -d")
        return

    # ------------------------------------------------------------------
    print("--- 1. Send messages without a key (round-robin across partitions) ---")
    for i in range(1, 6):
        msg = {"order_id": i, "item": f"item-{i}", "status": "placed", "ts": time.time()}
        future = producer.send(TOPIC, value=msg)
        meta = future.get(timeout=5)   # block to confirm delivery for demo clarity
        print(f"  sent order {i}  → partition={meta.partition}  offset={meta.offset}")

    # ------------------------------------------------------------------
    print("\n--- 2. Send messages with a key ---")
    print("    Same key always lands on the same partition — ordering guarantee.")
    for customer_id in ["cust-A", "cust-A", "cust-B", "cust-A", "cust-B"]:
        msg = {"customer": customer_id, "event": "page_view", "ts": time.time()}
        future = producer.send(TOPIC, key=customer_id, value=msg)
        meta = future.get(timeout=5)
        print(f"  customer={customer_id}  → partition={meta.partition}  offset={meta.offset}")

    # ------------------------------------------------------------------
    print("\n--- 3. Async send — buffer and flush at the end ---")
    futures = []
    for i in range(5):
        msg = {"batch_item": i, "ts": time.time()}
        futures.append(producer.send(TOPIC, value=msg))

    producer.flush()   # wait for all buffered messages
    print(f"  flushed {len(futures)} messages")

    producer.close()
    print(f"\nAll messages sent to topic '{TOPIC}'. Run 02_consumer.py to read them.")


if __name__ == "__main__":
    main()
