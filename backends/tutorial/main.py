from datetime import datetime, time, timedelta
import random
from uuid import UUID
from fastapi import (
    Body,
    Cookie,
    FastAPI,
    File,
    Form,
    HTTPException,
    Header,
    Query,
    Path,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from enum import Enum
from pydantic import BaseModel, AfterValidator, Field, HttpUrl
from typing import Annotated, Any, Literal


class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"


class Image(BaseModel):
    url: HttpUrl
    name: str


class Item(BaseModel):
    name: str = Field(examples=["Foo"])
    description: str | None = Field(default=None, examples=["A very nice Item"])
    price: float = Field(examples=[35.4])
    tax: float | None = Field(default=None, examples=[3.2])
    images: list[Image] | None = None


class Cookies(BaseModel):
    session_id: str
    fatebook_tracker: str | None = None
    googler_tracker: str | None = None


class CommonHeaders(BaseModel):
    host: str
    save_data: bool
    if_modified_since: str | None = None
    traceparent: str | None = None
    x_tag: list[str] = []


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

model_config = {
    "json_schema_extra": {
        "examples": [
            {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
            }
        ]
    }
}


@app.get("/")
async def root():
    content = """
<body>
<form action="/files/upload" enctype="multipart/form-data" method="post">
<input name="file" type="file">
<input type="submit">
</form>
<form action="/files/uploadfile/" enctype="multipart/form-data" method="post">
<input name="file" type="file">
<input type="submit">
</form>
</body>
    """

    return HTMLResponse(content=content)


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


@app.get("/users/{user_id}/items/{item_id}")
async def read_user_and_item(
    user_id: int, item_id: str, q: str | None = None, short: bool = False
):
    item = {"item_id": item_id, "owner_id": user_id}
    if q:
        item.update({"q": q})
    if not short:
        item.update(
            {"description": "This is an amazing item that has a long description"}
        )
    return item


@app.get("/needy_items/{item_id}")
async def read_user_item(
    item_id: str, needy: str, skip: int = 0, limit: int | None = None
):
    item = {"item_id": item_id, "needy": needy, "skip": skip, "limit": limit}
    return item


@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.dict()
    if item.tax:
        total_price = item.price + item.tax
        item_dict.update({"total_price": total_price})
    return item_dict


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item, q: str | None = None):
    result = {"item_id": item_id, **item.model_dump()}
    if q:
        result.update({"q": q})
    return result


@app.get("/items/limited/")
async def read_limited_items(
    q: Annotated[
        str | None, Query(min_length=3, max_length=50, pattern="^[a-zA-Z]+$")
    ] = None,
    q_list: Annotated[list[str] | None, Query(min_length=2, alias="q-list")] = None,
):
    results: dict[str, Any] = {"items": [{"item_id": "Foo"}, {"item_id": "Bar"}]}
    if q:
        results.update({"q": q})
    if q_list:
        results.update({"q_list": q_list})
    return results


data = {
    "isbn-9781529046137": "The Hitchhiker's Guide to the Galaxy",
    "imdb-tt0371724": "The Hitchhiker's Guide to the Galaxy",
    "isbn-9781439512982": "Isaac Asimov: The Complete Stories, Vol. 2",
}


def check_valid_id(id: str):
    if not id.startswith(("isbn-", "imdb-")):
        raise ValueError('Invalid ID format, it must start with "isbn-" or "imdb-"')
    return id


@app.get("/items/media/")
async def read_media_item(item_id: Annotated[str, AfterValidator(check_valid_id)]):
    if item_id in data:
        item = data.get(item_id)
    else:
        item_id, item = random.choice(list(data.items()))
    return {"id": item_id, "name": item}


@app.get("/items/validated/{item_id}")
async def read_validated_item(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=1, le=1000)],
    q: Annotated[str | None, Query(alias="item-query")] = None,
    size: Annotated[float | None, Query(gt=0, lt=10.5)] = None,
):
    results: dict[str, Any] = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if size:
        results.update({"size": size})
    return results


class FilterParams(BaseModel):
    model_config = {"extra": "forbid"}

    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


@app.get("/items/filter/model")
async def read_filtered_items(
    model: Annotated[FilterParams, Query(description="The model to filter by")],
):
    data = model.model_dump()
    return data


@app.put("/items/allparams/{item_id}")
async def update_allparams_item(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=0, le=1000)],
    q: str | None = None,
    item: Item | None = None,
):
    results: dict[str, Any] = {"item_id": item_id}
    if q:
        results.update({"q": q})
    if item:
        results.update({"item": item})
    return results


@app.put("/items/{item_id}/extra-data-types")
async def read_items_extra_data_types(
    item_id: UUID,
    start_datetime: Annotated[datetime, Body()],
    end_datetime: Annotated[datetime, Body()],
    process_after: Annotated[timedelta, Body()],
    repeat_at: Annotated[time | None, Body()] = None,
):
    start_process = start_datetime + process_after
    duration = end_datetime - start_process
    return {
        "item_id": item_id,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
        "process_after": process_after,
        "repeat_at": repeat_at,
        "start_process": start_process,
        "duration": duration,
    }


@app.get("/cookies/")
async def read_cookie_params(ads_id: Annotated[str | None, Cookie()] = None):
    return {"ads_id": ads_id}


@app.get("/cookies/model")
async def read_cookie_params_model(cookies: Annotated[Cookies, Cookie()]):
    return cookies


@app.get("/headers/")
async def read_header_params(
    user_agent: Annotated[str | None, Header()] = None,
    x_token: Annotated[list[str] | None, Header()] = None,
):
    return {"User-Agent": user_agent, "x-token": x_token}


@app.get("/headers/model")
async def read_header_params_model(headers: Annotated[CommonHeaders, Header()]):
    return headers


@app.post("/files/upload")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}


@app.post("/files/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename, "content_type": file.content_type}


@app.post("/files/form-and-file")
async def create_file_with_token(
    file: Annotated[bytes, File()],
    fileb: Annotated[UploadFile, File()],
    token: Annotated[str, Form()],
):
    return {
        "file_size": len(file),
        "token": token,
        "fileb_content_type": fileb.content_type,
    }


@app.get("/errors/not-found/{item_id}")
async def not_found(item_id: int):
    raise HTTPException(status_code=404, detail=f"Item with id {item_id} not found")


class CustomException(Exception):
    def __init__(self, value: int):
        self.value = value


@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(
        status_code=418,
        content={
            "message": f"Oops! {exc.value} did something. There goes a rainbow..."
        },
    )


@app.get("/errors/bad-request")
async def custom_error(value: int):
    raise CustomException(value=value)
