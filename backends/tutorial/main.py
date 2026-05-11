from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/items/{item_id}")
async def read_item(item_id: str, q: str | None = None, short: bool = False):
    if q:
        return {"item_id": item_id, "q": q}
    if not short:
        return {"item_id": item_id, "short": short}
    return {"item_id": item_id}


@app.get("/models/{model_name}")
async def echo_message(model_name: ModelName):
    return {"model_name": model_name}


@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]
