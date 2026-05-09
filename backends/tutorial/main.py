from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum

class Messages(str, Enum):
    hello = "hello"
    goodbye = "goodbye"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World!"}

@app.get("/cool")
async def cool_message():
    return {"message": "You are cool!"}

@app.get("/{message}")
async def echo_message(message: Messages):
    return {"message": message}