import urllib.parse


def lambda_handler(event, context):
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key    = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        size   = record["s3"]["object"].get("size", "unknown")
        print(f"[s3_processor] New object: s3://{bucket}/{key}  ({size} bytes)")

    return {"processed": len(event.get("Records", []))}
