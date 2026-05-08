from fastapi import FastAPI
from enum import Enum

class Messages(str, Enum):
    hello = "hello"
    goodbye = "goodbye"

app = FastAPI()

@app.get("/cool")
async def cool_message():
    return {"message": "You are cool!"}

@app.get("/{message}")
async def echo_message(message: Messages):
    return {"message": message}