from fastapi import FastAPI

app = FastAPI()

@app.get("/cool")
async def cool_message():
    return {"message": "You are cool!"}

@app.get("/{message}")
async def echo_message(message: str):
    return {"message": message}