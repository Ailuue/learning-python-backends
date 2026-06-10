# Webhooks

## What is this?

A webhook is an HTTP callback — you give a third-party service a URL, and it POSTs to that URL whenever something happens. When Stripe processes a payment, when GitHub merges a PR, when Twilio delivers an SMS: they fire a POST to your server with the event details. No polling, no long-lived connection.

The pattern looks simple: it's just an HTTP POST. The real complexity lives in the edges — fake payloads, duplicate delivery, failed deliveries that need retrying.

## The two sides

Every webhook interaction has two actors:

| Role | Job | You are this when… |
|---|---|---|
| **Receiver** | Accepts the POST, processes the event | Integrating with Stripe, GitHub, Twilio |
| **Sender** | Fires a POST when an event occurs | Building a platform that notifies others |

Most backend work is receiver-side. But understanding the sender side explains *why* receivers are designed the way they are.

## What the files cover

| File | What it teaches |
|---|---|
| `01_receiver.py` | Accept a POST, ack immediately, process async |
| `02_sender.py` | Webhook registry, fire events to registered URLs |
| `03_signing.py` | HMAC-SHA256 signing + verification, replay attack prevention |
| `04_reliability.py` | Retry with exponential backoff, idempotency on the receiver |

## How to run

```bash
pip install -r requirements.txt
```

**File 01 — receiver only**
```bash
uvicorn 01_receiver:app --port 8001 --reload

# Test with curl:
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"event": "order.created", "id": "evt_001", "data": {"order_id": 42}}'

curl http://localhost:8001/events
```

**Files 01 + 02 — sender firing to receiver** *(two terminals)*
```bash
# Terminal 1
uvicorn 01_receiver:app --port 8001 --reload

# Terminal 2
uvicorn 02_sender:app --port 8000 --reload

# Register the receiver as a webhook listener
curl -X POST "http://localhost:8000/webhooks/register?url=http://localhost:8001/webhook"

# Create an order — fires a webhook to all registered URLs
curl -X POST "http://localhost:8000/orders?item=keyboard"

# See what the receiver got
curl http://localhost:8001/events
```

**File 03 — signing** *(no server needed)*
```bash
python 03_signing.py
```

**File 04 — retries + idempotency** *(two terminals)*
```bash
# Terminal 1
uvicorn 04_reliability:receiver_app --port 8001 --reload

# Terminal 2
uvicorn 04_reliability:sender_app --port 8000 --reload

# Register both endpoints
curl -X POST "http://localhost:8000/webhooks/register?url=http://localhost:8001/webhook"
curl -X POST "http://localhost:8000/webhooks/register?url=http://localhost:8001/flaky"

# Fire an order and watch retry backoff in the sender terminal
curl -X POST "http://localhost:8000/orders?item=headphones"

# Flaky endpoint fails twice then succeeds.
# /processed count should be 1, not 3 — idempotency at work.
curl http://localhost:8001/processed
```

## Key concepts

**Acknowledge fast, process async.** Senders have short timeouts (5–30s). If your endpoint takes too long, the sender retries — and now you're processing it twice. Return `200` immediately and do the work in a background task or queue.

**HMAC signatures.** The sender signs the payload body with a shared secret. The receiver recomputes the HMAC and rejects anything that doesn't match. Use `hmac.compare_digest` (not `==`) to prevent timing attacks.

**Replay protection.** Signatures alone don't stop someone replaying a valid old event verbatim. Include the current timestamp in the signed content; reject events older than ~5 minutes.

**At-least-once delivery.** Senders retry on failure, which means you *will* sometimes receive duplicates — even on success, if the receiver processed the event but returned 500. This is a feature: it prevents silent event loss.

**Idempotency.** Your receiver must handle duplicates safely. Record processed event IDs (in memory, Redis, or a DB) and skip any event you've already seen. Use the sender's `id` field as the deduplication key.
