# SNS — Simple Notification Service

SNS is a pub/sub service. A publisher sends a message to a **topic**, and SNS fans it out to all subscribers simultaneously.
Subscribers can be SQS queues, HTTP endpoints, email addresses, Lambda functions, and more.

## Key concepts

- **Topic** — a named channel. Publishers send to a topic; they don't care who's subscribed.
- **Subscription** — registers a consumer (SQS queue, email, HTTP URL, Lambda) to receive messages from a topic.
- **Fan-out** — the core pattern: one SNS message → multiple SQS queues in parallel. Each queue processes independently.
- **Message filtering** — subscriptions can declare a filter policy so they only receive messages matching certain attributes. Avoids building routing logic in the consumer.

## SNS vs SQS

| | SNS | SQS |
|---|---|---|
| Pattern | Pub/sub (push to many) | Queue (pull by one consumer) |
| Delivery | Immediate fan-out to all subscribers | Stored until a consumer polls |
| Ordering | No guarantees | FIFO queues: yes |
| Use when | Broadcasting events (order placed → billing + inventory + email) | Worker queues, rate-limiting, retry logic |

## What the files cover

| File | What it teaches |
|------|----------------|
| `01_topics.py` | Create, list, describe, and delete topics |
| `02_publish.py` | Publish messages with message attributes and subject |
| `03_fan_out.py` | Fan-out pattern: one SNS topic → two SQS queues with filter policies |

## How to run

```bash
python sns/01_topics.py
python sns/02_publish.py
python sns/03_fan_out.py
```
