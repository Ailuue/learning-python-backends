# gRPC Deep Dive

> 📚 [Backend Learning](../README.md) · **Specialized topic** — best after the core path.

Remote procedure calls with Protocol Buffers and gRPC.

## What is gRPC?

gRPC is a framework for calling functions on a remote server as if they were local — no JSON, no URL design, no status-code mapping. You define your API as a `.proto` schema, generate strongly-typed client and server code, and call methods directly.

Under the hood it uses **HTTP/2** (multiplexed connections, header compression) and **Protocol Buffers** (binary, schema-validated serialization — much smaller and faster than JSON).

## The 4 RPC patterns

```
Unary              Client ──req──> Server ──res──> Client
Server streaming   Client ──req──> Server ──res1──res2──res3──> Client
Client streaming   Client ──req1──req2──req3──> Server ──res──> Client
Bidirectional      Client <──req1──res1──req2──res2──> Server  (both directions, simultaneously)
```

## Project layout

```
grpc-concepts/
  proto/                  ← .proto source files (edit these)
    greeter.proto         → used by 01, 05, 06
    stock.proto           → used by 02
    upload.proto          → used by 03
    chat.proto            → used by 04
  generate_protos.sh      ← compiles proto/ → *_pb2.py files (run once)
  requirements.txt
  01_unary.py
  02_server_streaming.py
  03_client_streaming.py
  04_bidirectional_streaming.py
  05_errors_and_metadata.py
  06_interceptors.py
```

## Setup

```bash
pip install -r requirements.txt
./generate_protos.sh      # compiles .proto files → *_pb2.py + *_pb2_grpc.py
```

You'll see new files appear: `greeter_pb2.py`, `greeter_pb2_grpc.py`, etc.
Never edit these — they're generated. Edit the `.proto` files and re-run the script.

## Running each concept

Every file is self-contained: it starts a server in the background, runs client calls, and exits.

```bash
python 01_unary.py
python 02_server_streaming.py
python 03_client_streaming.py
python 04_bidirectional_streaming.py
python 05_errors_and_metadata.py
python 06_interceptors.py
```

## Concept files

| File | Pattern | What you'll learn |
|------|---------|-------------------|
| [01_unary.py](01_unary.py) | Unary | Service definition, channel, stub, `context.abort()`, deadlines |
| [02_server_streaming.py](02_server_streaming.py) | Server stream | `yield` in servicer, iterating responses, `cancel()`, timeout |
| [03_client_streaming.py](03_client_streaming.py) | Client stream | Generator as request, server accumulates, single response |
| [04_bidirectional_streaming.py](04_bidirectional_streaming.py) | Bidi stream | Full-duplex, `request_iterator` + `yield`, early cancel |
| [05_errors_and_metadata.py](05_errors_and_metadata.py) | Unary | Status codes, `invocation_metadata`, `send_initial_metadata`, `future()` |
| [06_interceptors.py](06_interceptors.py) | Unary | Server auth+logging interceptors, client token-injection interceptor |

## Key concepts at a glance

### Defining a service

```proto
service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);           // unary
  rpc StreamPrices (SubscribeRequest) returns (stream Price); // server streaming
  rpc UploadFile (stream Chunk) returns (UploadResult);       // client streaming
  rpc Connect (stream Msg) returns (stream Msg);              // bidirectional
}
```

### Server skeleton

```python
class MyServicer(my_pb2_grpc.MyServiceServicer):
    def MyMethod(self, request, context):          # unary
        return my_pb2.Response(value=42)

    def MyStream(self, request, context):          # server streaming
        for item in data:
            yield my_pb2.Response(value=item)

    def MyUpload(self, request_iterator, context): # client streaming
        for chunk in request_iterator:
            process(chunk)
        return my_pb2.Summary(total=n)

server = grpc.server(futures.ThreadPoolExecutor())
my_pb2_grpc.add_MyServiceServicer_to_server(MyServicer(), server)
server.add_insecure_port("[::]:50051")
server.start()
server.wait_for_termination()
```

### Client skeleton

```python
with grpc.insecure_channel("localhost:50051") as channel:
    stub = my_pb2_grpc.MyServiceStub(channel)
    reply = stub.MyMethod(my_pb2.Request(name="Alex"), timeout=5)
```

### Status codes

```python
# Server — abort the RPC
context.abort(grpc.StatusCode.NOT_FOUND, "user 99 not found")

# Client — catch it
try:
    stub.GetUser(...)
except grpc.RpcError as e:
    e.code()     # grpc.StatusCode.NOT_FOUND
    e.details()  # "user 99 not found"
```

### Metadata (request headers)

```python
# Client sends metadata
stub.SayHello(req, metadata=[("authorization", "my-token")])

# Server reads it
meta = dict(context.invocation_metadata())
token = meta.get("authorization")

# Server sends metadata back
context.send_initial_metadata([("x-request-id", "abc")])
context.set_trailing_metadata([("x-duration-ms", "12")])

# Client reads response metadata via future
future = stub.SayHello.future(req)
future.initial_metadata()
future.trailing_metadata()
```

### Interceptors

```python
# Server interceptors
server = grpc.server(
    futures.ThreadPoolExecutor(),
    interceptors=[AuthInterceptor(), LoggingInterceptor()],
)

# Client interceptors
channel = grpc.intercept_channel(
    grpc.insecure_channel("localhost:50051"),
    TokenInjectorInterceptor("my-token"),
)
```
