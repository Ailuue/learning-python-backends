"""
Consumer Groups — Work Queue vs Fan-Out
=========================================
Consumer groups are the most important Kafka concept to understand.
They control who gets each message.

Work queue (same group_id)
    Multiple consumers share one group_id. Kafka assigns each partition to
    exactly one consumer in the group. Each message is processed by ONE consumer.
    This is horizontal scaling — add more consumers to handle more load.

    Producer ──▶ Topic (3 partitions)
                 Partition 0 ──▶ Consumer A  ┐
                 Partition 1 ──▶ Consumer B  ├── group: "processors"
                 Partition 2 ──▶ Consumer A  ┘

Fan-out / Pub-Sub (different group_ids)
    Multiple groups each get their own copy of every message.
    Use this when different subsystems all need to react to the same event.

    Producer ──▶ Topic
                       ──▶ Consumer A  (group: "email-service")    → sends email
                       ──▶ Consumer B  (group: "analytics-service") → logs to DB
                       ──▶ Consumer C  (group: "audit-log")         → writes audit

    This is impossible with a traditional message queue (RabbitMQ/SQS):
    once a queue consumer reads a message, it's gone. Kafka's log-based
    storage makes fan-out free — each group just tracks its own offset.

This script spawns consumers as threads so you can see both patterns
without opening multiple terminals.

Prerequisites:
    docker compose up -d
    python 01_producer.py   (seed some messages first)

Run:
    python 03_consumer_groups.py
"""

import json
import threading
import time

from kafka import KafkaConsumer, KafkaProducer

BOOTSTRAP = "localhost:9092"
TOPIC = "events"


def make_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode(),
    )


def run_consumer(name: str, group_id: str, results: list, max_messages: int = 5):
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        value_deserializer=lambda v: json.loads(v.decode()) if v else None,
        consumer_timeout_ms=4000,
    )
    for message in consumer:
        entry = f"[{name}] offset={message.offset}  {message.value}"
        results.append(entry)
        if len(results) >= max_messages:
            break
    consumer.close()


def demo_work_queue():
    """
    Two consumers share one group. Each message goes to exactly one of them.
    Kafka's partition assignment balances the load.
    """
    print("\n=== WORK QUEUE: same group_id ===")
    print("    Two consumers compete for messages. Each message processed once.\n")

    # Produce 10 messages
    producer = make_producer()
    for i in range(10):
        producer.send(TOPIC, value={"event": "order", "id": i})
    producer.flush()
    producer.close()
    time.sleep(0.5)

    results_a, results_b = [], []
    group = "work-queue-group"

    t_a = threading.Thread(target=run_consumer, args=("Worker-A", group, results_a, 10))
    t_b = threading.Thread(target=run_consumer, args=("Worker-B", group, results_b, 10))
    t_a.start()
    t_b.start()
    t_a.join()
    t_b.join()

    all_results = sorted(results_a + results_b, key=lambda s: int(s.split("offset=")[1].split(" ")[0]))
    for r in all_results:
        print(f"  {r}")

    print(f"\n  Worker-A processed: {len(results_a)} messages")
    print(f"  Worker-B processed: {len(results_b)} messages")
    print(f"  Total: {len(results_a) + len(results_b)} (each message processed exactly once)")


def demo_fanout():
    """
    Two consumers have different group_ids. Each gets all messages independently.
    Adding a third group doesn't affect the other two.
    """
    print("\n=== FAN-OUT: different group_ids ===")
    print("    Two independent services each receive every message.\n")

    # Use the same messages already in the topic by resetting to earliest
    results_email, results_analytics = [], []

    t_email = threading.Thread(
        target=run_consumer,
        args=("EmailService", "email-service", results_email, 10)
    )
    t_analytics = threading.Thread(
        target=run_consumer,
        args=("Analytics ", "analytics-service", results_analytics, 10)
    )
    t_email.start()
    t_analytics.start()
    t_email.join()
    t_analytics.join()

    print("  EmailService received:")
    for r in results_email:
        print(f"    {r}")
    print("\n  Analytics received:")
    for r in results_analytics:
        print(f"    {r}")
    print(f"\n  Both groups got all {len(results_email)} messages independently.")


def main():
    demo_work_queue()
    demo_fanout()


if __name__ == "__main__":
    main()
