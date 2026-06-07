# Lambda

Lambda is serverless compute. You write a function, deploy it, and AWS runs it in response to events —
no servers to provision or manage. You pay only for the time the function actually runs.

## Key concepts

- **Function** — a unit of code with a handler (entry point), runtime, and memory/timeout config.
- **Handler** — the entry point, specified as `module.function`. For `handler.py` with `def lambda_handler(event, context)`, it's `handler.lambda_handler`.
- **Event** — the input passed to the function. Shape depends on the trigger (API Gateway, S3, SQS, etc.).
- **Context** — metadata about the invocation (function name, remaining time, request ID).
- **Invocation types:**
  - `RequestResponse` — synchronous. Caller waits for the result.
  - `Event` — asynchronous. Lambda queues the event and returns immediately.
- **Trigger / event source mapping** — wires an AWS service to Lambda so events automatically invoke the function.

## Lambda in LocalStack

LocalStack runs Lambda functions in Docker containers. Requires the Docker socket mount in `docker-compose.yml`
(already included). First invocation of a new function is slow — Docker pulls the runtime image.

## What the files cover

| File | What it teaches |
|------|----------------|
| `01_deploy.py` | Package code into a zip, create a function, update it |
| `02_invoke.py` | Invoke synchronously and asynchronously, parse response |
| `03_s3_trigger.py` | Wire an S3 bucket to trigger a Lambda on object upload |

## How to run

```bash
python lambda/01_deploy.py
python lambda/02_invoke.py
python lambda/03_s3_trigger.py
```
