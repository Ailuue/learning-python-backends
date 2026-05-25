from fastapi import FastAPI

app = FastAPI(title="Docker Practice API")


@app.get("/")
def root():
    return {"message": "Hello from Docker!", "stage": "multi-stage build"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items/{item_id}")
def get_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
