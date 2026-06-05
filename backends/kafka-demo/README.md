# Kafka

## What is this?

Imagine a newspaper. The newspaper is printed once, but thousands of people can each read their own copy. Nobody's reading "uses up" the newspaper — it just sits there until its expiry date.

**Apache Kafka** works like this for data. It's a system where applications can publish messages to named **topics** (like publishing to a newspaper), and any number of other applications can read from those topics independently. Unlike a traditional message queue where a message disappears once consumed, Kafka keeps messages in an ordered log for a configurable amount of time. Any consumer can read, rewind, and replay.

This makes Kafka the backbone of event-driven architectures: when something happens in your system ("order placed", "user signed up", "payment failed"), you publish an event to Kafka, and every service that cares about that event gets its own copy.

## Key concepts

**Topic** — a named stream of messages. Like a table in a database, but append-only and time-ordered.

**Producer** — an application that writes messages to a topic.

**Consumer** — an application that reads messages from a topic.

**Partition** — topics are split into partitions for parallelism. Messages with the same key always go to the same partition, guaranteeing their order relative to each other.

**Consumer group** — a group of consumers that share the work of reading a topic. This is the most important concept in Kafka:
- **Same group** → work queue: each message is processed by exactly one consumer. Add more consumers to scale.
- **Different groups** → fan-out: each group gets its own independent copy of every message.

**Offset** — a consumer's position in the log. Kafka remembers where you left off so you can resume after a restart.

## Why use Kafka instead of just calling the other service directly?

- **Decoupling**: the order service doesn't need to know about the email service, the analytics service, or the inventory service. It just publishes "order placed."
- **Resilience**: if the email service is down, the message waits in Kafka. Nothing is lost.
- **Replay**: if analytics needs to reprocess the last 7 days of events, it can — the data is still there.
- **Scale**: partition a topic across many brokers; run many consumers in parallel.

## What the files cover

| File | What it teaches |
|---|---|
| `01_producer.py` | Sending messages to a topic; keyed vs unkeyed; sync vs batched flush |
| `02_consumer.py` | Reading messages; offsets; auto-commit vs manual commit; replaying from the start |
| `03_consumer_groups.py` | The critical concept: same group = work queue, different groups = fan-out |
| `04_partitions.py` | How message keys determine which partition a message lands on, and why ordering depends on it |
| `05_fastapi.py` | A FastAPI app that publishes events on HTTP requests (returns 202 immediately) |
| `worker.py` | A separate process that consumes and processes those events asynchronously |

## How to run

```bash
# Start Kafka (KRaft mode — no Zookeeper needed)
docker compose up -d

pip install -r requirements.txt

# Work through the files in order:
python 01_producer.py
python 02_consumer.py
python 03_consumer_groups.py
python 04_partitions.py

# FastAPI + worker (open two terminals):
uvicorn 05_fastapi:app --reload    # terminal 1
python worker.py                   # terminal 2

# Post an order and watch the worker process it:
curl -s -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{"item": "keyboard", "quantity": 1, "customer_id": "cust-1"}' | python -m json.tool
```
