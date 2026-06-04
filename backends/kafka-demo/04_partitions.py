"""
Partitions and Message Keys
=============================
A topic is split into partitions for parallelism. Each partition is an
ordered, append-only log. Ordering is guaranteed *within* a partition but
NOT across partitions.

    Topic: user-events (3 partitions)

    Partition 0: [e1, e4, e7, ...]   ← all events for user-A
    Partition 1: [e2, e5, e8, ...]   ← all events for user-B
    Partition 2: [e3, e6, e9, ...]   ← all events for user-C

Message keys and routing
    No key → round-robin across partitions (default)
    With key → hash(key) % num_partitions → deterministic assignment

    Why keys matter: if you send "user-A: add item" then "user-A: checkout"
    without a key, they could land on different partitions and be consumed
    out of order. With key=user-A, both go to the same partition and are
    always consumed in order.

    Rule of thumb: key = the entity whose events must be ordered.
    Common choices: user_id, order_id, device_id, session_id.

Partition count vs consumer count
    Parallelism is bounded by partition count. If a topic has 3 partitions,
    at most 3 consumers in a group can work in parallel. Adding a 4th
    consumer to the group leaves it idle.

    You can increase partitions later, but this breaks key-to-partition
    assignments (hash(key) % new_count differs). Plan partition count upfront
    for high-throughput topics.

Prerequisites:
    docker compose up -d

Run:
    python 04_partitions.py
"""

import json
import time

from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError

BOOTSTRAP = "localhost:9092"
TOPIC = "user-events"
NUM_PARTITIONS = 3


def ensure_topic():
    admin = KafkaAdminClient(bootstrap_servers=BOOTSTRAP)
    try:
        admin.create_topics([NewTopic(TOPIC, num_partitions=NUM_PARTITIONS, replication_factor=1)])
        print(f"  Created topic '{TOPIC}' with {NUM_PARTITIONS} partitions")
    except TopicAlreadyExistsError:
        print(f"  Topic '{TOPIC}' already exists")
    finally:
        admin.close()


def produce_keyed(events: list[tuple[str, dict]]) -> list[tuple[str, int, int]]:
    """Send (key, value) pairs and return (key, partition, offset) for each."""
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
        key_serializer=lambda k: k.encode() if k else None,
    )
    results = []
    for key, value in events:
        future = producer.send(TOPIC, key=key, value=value)
        meta = future.get(timeout=5)
        results.append((key, meta.partition, meta.offset))
    producer.flush()
    producer.close()
    return results


def main():
    print("=== Kafka Partitions and Message Keys ===\n")

    ensure_topic()

    # ------------------------------------------------------------------
    print("\n--- 1. Keyed messages: same key → same partition (ordering guaranteed) ---")
    events = [
        ("user-A", {"event": "login",       "user": "A"}),
        ("user-B", {"event": "login",       "user": "B"}),
        ("user-A", {"event": "add_to_cart", "user": "A"}),
        ("user-C", {"event": "login",       "user": "C"}),
        ("user-B", {"event": "purchase",    "user": "B"}),
        ("user-A", {"event": "checkout",    "user": "A"}),
        ("user-C", {"event": "add_to_cart", "user": "C"}),
    ]

    results = produce_keyed(events)
    for key, partition, offset in results:
        print(f"  key={key:<8s}  → partition={partition}  offset={offset}")

    # Group by key to show consistent assignment
    from collections import defaultdict
    by_key: dict[str, set] = defaultdict(set)
    for key, partition, _ in results:
        by_key[key].add(partition)

    print("\n  Summary: each key consistently maps to one partition")
    for key, partitions in sorted(by_key.items()):
        print(f"    {key}: partitions used = {partitions}  (always 1 partition per key)")

    # ------------------------------------------------------------------
    print("\n--- 2. Unkeyed messages: round-robin across partitions ---")
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
    )
    print("  (no ordering guarantee — messages may be consumed out of send order)")
    for i in range(6):
        msg = {"event": "anonymous_action", "seq": i}
        meta = producer.send(TOPIC, value=msg).get(timeout=5)
        print(f"  seq={i}  → partition={meta.partition}  offset={meta.offset}")
    producer.flush()
    producer.close()

    # ------------------------------------------------------------------
    print("\n--- 3. Consuming from a specific partition ---")
    print("    Assigning directly to partition 0 (bypasses consumer group balancing)")
    from kafka import TopicPartition
    consumer = KafkaConsumer(
        bootstrap_servers=BOOTSTRAP,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode()),
        key_deserializer=lambda k: k.decode() if k else None,
        consumer_timeout_ms=2000,
    )
    consumer.assign([TopicPartition(TOPIC, 0)])
    consumer.seek_to_beginning()

    messages = list(consumer)
    consumer.close()

    print(f"  Partition 0 contains {len(messages)} messages:")
    for m in messages:
        print(f"    offset={m.offset}  key={m.key or '(none)':10s}  value={m.value}")


if __name__ == "__main__":
    main()
