"""
100 posts seeded for pagination demos.
"""

import base64

_SEED = [
    {"id": str(i), "title": f"Post {i:03d}", "body": f"Body of post {i}", "tags": ["python", "graphql"] if i % 2 == 0 else ["backend"]}
    for i in range(1, 101)
]

posts: list[dict] = [r.copy() for r in _SEED]


def reset() -> None:
    global posts
    posts = [r.copy() for r in _SEED]


def encode_cursor(post_id: str) -> str:
    return base64.b64encode(f"post:{post_id}".encode()).decode()


def decode_cursor(cursor: str) -> str:
    payload = base64.b64decode(cursor.encode()).decode()
    return payload.split(":", 1)[1]  # "post:42" → "42"


reset()
