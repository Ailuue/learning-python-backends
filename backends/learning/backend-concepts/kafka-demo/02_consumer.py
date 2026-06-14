"""
Kafka Consumer
===============
A consumer reads messages from a topic by polling the broker. It tracks
its position using an *offset* — the index of the last message it processed.
Kafka stores this offset so the consumer can resume after a restart.

    Topic: orders  (Partition 0)
    ┌──────┬──────┬──────┬──────┬──────┬──────┐
    │ msg0 │ msg1 │ msg2 │ msg3 │ msg4 │ msg5 │
    └──────┴──────┴──────┴──────┴──────┴──────┘
                                ↑
                     committed offset = 4
                     (consumer has processed 0-3, next poll returns 4+)

auto_offset_reset
    "earliest" — start from the very first message (replay the full log)
    "latest"   — start from new messages only (skip history)

Offset commits
    auto-commit (default, enable_auto_commit=True)
        Kafka commits the offset periodically in the background.
        Risk: if your process crashes after polling but before processing,
        the offset is already committed — those messages are skipped on restart.

    manual commit (enable_auto_commit=False, consumer.commit())
        You commit only after successfully processing a message.
        Safer: worst case is re-processing (at-least-once delivery).

Prerequisites:
    docker compose up -d
    python 01_producer.py   (to have messages to consume)

Run:
    python 02_consumer.py
    (Press Ctrl-C to stop.)
"""

import json

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

BOOTSTRAP = "localhost:9092"
TOPIC = "orders"
GROUP_ID = "demo-consumer-group"


def make_consumer(group_id: str, from_beginning: bool = True) -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=group_id,
        auto_offset_reset="earliest" if from_beginning else "latest",
        enable_auto_commit=False,   # manual commit — we control exactly when
        value_deserializer=lambda v: json.loads(v.decode()),
        key_deserializer=lambda k: k.decode() if k else None,
        consumer_timeout_ms=3000,   # stop polling after 3s of no messages (for demo)
    )


def process(message) -> None:
    """Simulate processing — replace with real business logic."""
    key = message.key or "(no key)"
    print(
        f"  partition={message.partition}  offset={message.offset:4d}"
        f"  key={key:<12s}  value={message.value}"
    )


def main():
    print("=== Kafka Consumer Demo ===\n")

    try:
        consumer = make_consumer(GROUP_ID, from_beginning=True)
    except NoBrokersAvailable:
        print("ERROR: Kafka not reachable. Run:  docker compose up -d")
        return

    print(f"Consuming topic='{TOPIC}'  group='{GROUP_ID}'  (Ctrl-C to stop)\n")
    print("--- Messages ---")

    count = 0
    try:
        for message in consumer:
            process(message)
            # Commit after processing — at-least-once delivery guarantee.
            # If the process crashes here, this message will be re-delivered.
            consumer.commit()
            count += 1
    except KeyboardInterrupt:
        pass

    print(f"\nProcessed {count} messages.")
    print("Offset is now committed. Re-running this script with the same")
    print(f"group_id='{GROUP_ID}' will NOT re-read these messages.")
    print("To re-read from the beginning, change group_id to something new.")
    consumer.close()


if __name__ == "__main__":
    main()
