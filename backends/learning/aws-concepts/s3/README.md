# S3 — Simple Storage Service

S3 is object storage. You store arbitrary files (objects) inside named containers (buckets).
There is no filesystem hierarchy — keys like `data/users/123.json` just look like paths, but S3 treats them as flat strings.

## Key concepts

- **Bucket** — a globally unique named container. You create one per environment, app, or purpose.
- **Object** — any file + its metadata, addressed by a key (string). Max size 5TB.
- **Key** — the object's "path" within a bucket, e.g. `uploads/2024/photo.jpg`.
- **Presigned URL** — a time-limited URL that grants temporary access to a specific object without requiring AWS credentials. Used for secure file uploads/downloads from browsers or third parties.

## What the files cover

| File | What it teaches |
|------|----------------|
| `01_buckets.py` | Create, list, tag, and delete buckets |
| `02_objects.py` | Upload, list (with prefix), download, copy, delete objects |
| `03_presigned_urls.py` | Generate GET, PUT, and POST presigned URLs |

## How to run

```bash
# From aws-concepts/
docker compose up -d

python s3/01_buckets.py
python s3/02_objects.py
python s3/03_presigned_urls.py
```
