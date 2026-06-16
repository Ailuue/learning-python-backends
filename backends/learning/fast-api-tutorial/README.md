# FastAPI Tutorial

> 📚 [Backend Learning](../README.md) · **Core path · step 1 of 4** · Next: [testing-concepts ➡](../testing-concepts/)

Working through the official FastAPI documentation from basics to advanced patterns.

## Structure

```
tutorial/   — core FastAPI concepts (follows the official tutorial order)
advanced/   — advanced user guide topics
```

## What's covered

### tutorial/
A single growing `main.py` that adds one concept at a time:
- Path parameters, query parameters, request bodies
- Pydantic models and validation
- Response models and status codes
- Form data, file uploads, cookies, headers
- `Depends` for dependency injection
- Path operations with `APIRouter`
- Background tasks
- Middleware

### advanced/
- Custom request/response handling
- Advanced dependencies (with `yield`, class-based)
- `Request` object access
- Cookies and sessions
- Security utilities

## Running

```bash
# Run the tutorial app
uvicorn tutorial.main:app --reload

# Run the advanced app
uvicorn advanced.main:app --reload --port 8001
```

Interactive docs at http://localhost:8000/docs.
