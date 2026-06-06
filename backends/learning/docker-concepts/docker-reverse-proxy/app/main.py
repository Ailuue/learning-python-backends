from fastapi import FastAPI, Request

app = FastAPI(title="Reverse Proxy Practice API")


@app.get("/")
def root(request: Request):
    return {
        "message": "Hello from behind nginx!",
        "x_real_ip": request.headers.get("X-Real-IP", "not set"),
        "x_forwarded_for": request.headers.get("X-Forwarded-For", "not set"),
        "x_forwarded_proto": request.headers.get("X-Forwarded-Proto", "not set"),
        "host": request.headers.get("Host", "not set"),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/headers")
def show_headers(request: Request):
    """Show all request headers — useful for seeing what nginx passes through."""
    return dict(request.headers)
