from fastapi import FastAPI

app = FastAPI()


@app.get("/{message}")
async def root(message: str):
    return {"message": message}