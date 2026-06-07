# SQS — Simple Queue Service

SQS is a managed message queue. Producers push messages onto a queue; consumers poll the queue and process them.
It decouples services: the producer doesn't care whether the consumer is running or how fast it processes.

## Key concepts

- **Queue** — a buffer of messages. Two types:
  - **Standard** — at-least-once delivery, best-effort ordering. High throughput.
  - **FIFO** — exactly-once delivery, strict ordering. Lower throughput, requires `.fifo` suffix.
- **Visibility timeout** — after a consumer receives a message, it becomes invisible to other consumers for N seconds. If the consumer doesn't delete it in time, it reappears (gets retried). This prevents double-processing.
- **Dead letter queue (DLQ)** — a separate queue for messages that fail processing too many times. Essential for debugging and preventing poison-pill messages from blocking the queue forever.
- **Long polling** — instead of returning empty immediately, SQS waits up to 20s for a message to arrive. Reduces empty responses and API costs.

## What the files cover

| File | What it teaches |
|------|----------------|
| `01_queues.py` | Create standard and FIFO queues, read attributes, delete |
| `02_messages.py` | Send, receive, delete messages; visibility timeout behaviour |
| `03_dead_letter.py` | Wire a DLQ, simulate failures, inspect stuck messages |

## How to run

```bash
python sqs/01_queues.py
python sqs/02_messages.py
python sqs/03_dead_letter.py
```
