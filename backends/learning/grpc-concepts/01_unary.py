"""
Concept 01 — Unary RPC

gRPC is a high-performance RPC framework built on HTTP/2 and Protocol Buffers.
Instead of defining routes and JSON payloads, you define services and messages
in a .proto schema and generate strongly-typed client/server code from it.

UNARY RPC — the simplest pattern:
  Client sends one request → Server sends one response

This is analogous to a normal HTTP GET/POST. Compared to REST:
  REST:  POST /users  {"name": "Alex"}  → 200 {"id": 1, "name": "Alex"}
  gRPC:  SayHello(HelloRequest{name:"Alex"}) → HelloReply{message:"Hello, Alex"}

Key pieces generated from greeter.proto:
  greeter_pb2.py        — message classes (HelloRequest, HelloReply, User, ...)
  greeter_pb2_grpc.py   — GreeterServicer (base class to implement),
                          GreeterStub (client),
                          add_GreeterServicer_to_server() (registers server)

HOW TO RUN:
  pip install -r requirements.txt
  ./generate_protos.sh        ← only needed once
  python 01_unary.py
"""

import time
import threading
import grpc
from concurrent import futures

import greeter_pb2
import greeter_pb2_grpc

PORT = 50051


# ---------------------------------------------------------------------------
# Server implementation
# ---------------------------------------------------------------------------
# Subclass the generated Servicer to implement each RPC method.
# Each method receives (request, context) — context carries metadata,
# deadline, peer address, and lets you set error codes.

class GreeterServicer(greeter_pb2_grpc.GreeterServicer):

    def SayHello(self, request, context):
        print(f"  [server] SayHello called: name={request.name!r}")
        return greeter_pb2.HelloReply(message=f"Hello, {request.name}!")

    def GetUser(self, request, context):
        print(f"  [server] GetUser called: user_id={request.user_id}")
        # Simulate a database lookup
        users = {
            1: greeter_pb2.User(id=1, name="Alex",  email="alex@example.com"),
            2: greeter_pb2.User(id=2, name="Dana",  email="dana@example.com"),
        }
        if request.user_id not in users:
            # context.abort() immediately ends the RPC with an error code.
            # (See 05_errors_and_metadata.py for a full error-handling tour.)
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.user_id} not found")
        return users[request.user_id]


def make_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    greeter_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    return server


# ---------------------------------------------------------------------------
# Client calls
# ---------------------------------------------------------------------------

def run_client():
    # A channel is the connection to the server.
    # insecure_channel = no TLS (fine for local dev; use secure_channel in prod).
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = greeter_pb2_grpc.GreeterStub(channel)

        # ── SayHello ────────────────────────────────────────────────────────
        print("\n1. SayHello:")
        reply = stub.SayHello(greeter_pb2.HelloRequest(name="Alex"))
        # reply is a strongly-typed HelloReply message, not a dict
        print(f"   response.message = {reply.message!r}")

        # ── GetUser ─────────────────────────────────────────────────────────
        print("\n2. GetUser (existing user):")
        user = stub.GetUser(greeter_pb2.GetUserRequest(user_id=1))
        print(f"   id={user.id}  name={user.name!r}  email={user.email!r}")

        # ── GetUser (missing user) ───────────────────────────────────────────
        print("\n3. GetUser (missing user — expect NOT_FOUND):")
        try:
            stub.GetUser(greeter_pb2.GetUserRequest(user_id=99))
        except grpc.RpcError as e:
            print(f"   status code:    {e.code()}")
            print(f"   status details: {e.details()}")

        # ── Deadline / timeout ───────────────────────────────────────────────
        # Every RPC can carry a deadline. If the server exceeds it, the client
        # gets DEADLINE_EXCEEDED. Pass timeout= (seconds) to any stub call.
        print("\n4. SayHello with a tight deadline:")
        try:
            reply = stub.SayHello(
                greeter_pb2.HelloRequest(name="Timeout Test"),
                timeout=0.0001,   # 0.1 ms — will almost certainly expire
            )
        except grpc.RpcError as e:
            print(f"   status code:    {e.code()}")   # DEADLINE_EXCEEDED


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 01 — Unary RPC")
    print("=" * 60)

    server = make_server()
    server.start()
    time.sleep(0.1)   # give server a moment to bind

    try:
        run_client()
    finally:
        server.stop(grace=0)


if __name__ == "__main__":
    main()
