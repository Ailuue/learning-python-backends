# AWS Core Services with LocalStack

Practice the core AWS services locally — no AWS account or billing required.
LocalStack emulates AWS APIs on `http://localhost:4566`.

## Services covered

| Service | What it is |
|---------|-----------|
| S3 | Object storage — files, blobs, static assets |
| DynamoDB | NoSQL key-value + document database |
| SQS | Message queue — decouple services, buffer workloads |
| SNS | Pub/sub — broadcast messages to multiple consumers |
| Lambda | Serverless compute — run code in response to events |

## Setup

```bash
# 1. Start LocalStack
docker compose up -d

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify LocalStack is up (should return empty, no errors)
awslocal s3 ls
```

## Running scripts

Run any script from the `aws-concepts/` directory:

```bash
python s3/01_buckets.py
python dynamodb/02_crud.py
# etc.
```

Each script is self-contained: it sets up the resources it needs, demonstrates the concept, then cleans up.

## What the folders cover

| Folder | Files |
|--------|-------|
| `s3/` | Buckets, objects (upload/download/copy), presigned URLs |
| `dynamodb/` | Tables, CRUD operations, queries and scans |
| `sqs/` | Queues, messages + visibility timeout, dead letter queues |
| `sns/` | Topics, publish, fan-out (SNS → multiple SQS queues) |
| `lambda/` | Deploy a function, invoke it, trigger from S3 events |

## Community vs Pro

The free Community tier covers all services here. Notable limitations:
- **IAM** is a no-op — permissions are not enforced
- **RDS, ECS, EKS, ElastiCache** are Pro-only
- Lambda requires Docker socket access (already in the compose file)
