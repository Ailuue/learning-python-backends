"""
Concept 05 — Error Handling & Metadata

ERRORS
------
gRPC has its own status code system, separate from HTTP:

  OK               Normal success
  NOT_FOUND        Resource doesn't exist
  INVALID_ARGUMENT Bad input from the client
  UNAUTHENTICATED  Missing or invalid credentials
  PERMISSION_DENIED  Credentials valid but access denied
  ALREADY_EXISTS   Attempted to create something that already exists
  RESOURCE_EXHAUSTED  Rate limit or quota exceeded
  UNAVAILABLE      Server is temporarily down (safe to retry)
  DEADLINE_EXCEEDED  Timeout
  INTERNAL         Server-side bug (don't expose internals to the client)
  UNIMPLEMENTED    RPC exists in the proto but isn't implemented

Server raises an error with: context.abort(StatusCode, "details string")
Client catches it with:       except grpc.RpcError as e: e.code(), e.details()

METADATA
--------
Metadata is key-value pairs sent alongside an RPC call — the equivalent
of HTTP headers. Used for auth tokens, request IDs, tracing context, etc.

  Client → Server:  pass metadata= kwarg to the stub call
  Server → Client:  call context.send_initial_metadata() or
                    context.set_trailing_metadata()

Keys must be lowercase ASCII. Binary values use the "-bin" suffix convention.
The client reads response metadata via the call's future or trailing_metadata().

HOW TO RUN:
  ./generate_protos.sh   ← if you haven't yet
  python 05_errors_and_metadata.py
"""

import time
from concurrent import futures

import grpc

import greeter_pb2
import greeter_pb2_grpc

PORT = 50055

KNOWN_USERS = {
    1: greeter_pb2.User(id=1, name="Alex", email="alex@example.com"),
    2: greeter_pb2.User(id=2, name="Dana", email="dana@example.com"),
}


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class GreeterServicer(greeter_pb2_grpc.GreeterServicer):

    def SayHello(self, request, context):
        # Read metadata sent by the client
        client_meta = dict(context.invocation_metadata())
        request_id = client_meta.get("x-request-id", "unknown")
        lang = client_meta.get("accept-language", "en")
        print(f"  [server] SayHello  request-id={request_id}  lang={lang}")

        if not request.name:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "name must not be empty",
            )

        greeting = {"en": "Hello", "es": "Hola", "fr": "Bonjour"}.get(lang, "Hello")
        reply_text = f"{greeting}, {request.name}!"

        # Send initial metadata back to the client before the response body.
        # Useful for headers that the client needs before reading the result.
        context.send_initial_metadata([
            ("x-served-by", "greeter-server-1"),
            ("x-request-id", request_id),   # echo it back
        ])

        # Trailing metadata is sent after the response body (like HTTP trailers).
        context.set_trailing_metadata([
            ("x-processing-ms", "12"),
        ])

        return greeter_pb2.HelloReply(message=reply_text)

    def GetUser(self, request, context):
        if request.user_id <= 0:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"user_id must be positive, got {request.user_id}",
            )

        user = KNOWN_USERS.get(request.user_id)
        if user is None:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"user {request.user_id} does not exist",
            )

        return user


def make_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    greeter_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    return server


# ---------------------------------------------------------------------------
# Client helpers
# ---------------------------------------------------------------------------

def print_rpc_error(e: grpc.RpcError):
    print(f"   RpcError  code={e.code()}  details={e.details()!r}")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def run_client():
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = greeter_pb2_grpc.GreeterStub(channel)

        # ── 1. Sending client metadata ────────────────────────────────────
        print("\n1. SayHello with client metadata (request-id, language):")
        client_metadata = [
            ("x-request-id", "abc-123"),
            ("accept-language", "es"),     # server will greet in Spanish
        ]
        # Use a Future-style call to access response metadata
        future = stub.SayHello.future(
            greeter_pb2.HelloRequest(name="Alex"),
            metadata=client_metadata,
        )
        reply = future.result()
        print(f"   reply: {reply.message!r}")
        print(f"   initial metadata:  {dict(future.initial_metadata())}")
        print(f"   trailing metadata: {dict(future.trailing_metadata())}")

        # ── 2. INVALID_ARGUMENT ───────────────────────────────────────────
        print("\n2. SayHello with empty name (expect INVALID_ARGUMENT):")
        try:
            stub.SayHello(greeter_pb2.HelloRequest(name=""))
        except grpc.RpcError as e:
            print_rpc_error(e)

        # ── 3. NOT_FOUND ──────────────────────────────────────────────────
        print("\n3. GetUser for missing ID (expect NOT_FOUND):")
        try:
            stub.GetUser(greeter_pb2.GetUserRequest(user_id=99))
        except grpc.RpcError as e:
            print_rpc_error(e)

        # ── 4. INVALID_ARGUMENT (negative ID) ────────────────────────────
        print("\n4. GetUser with invalid ID (expect INVALID_ARGUMENT):")
        try:
            stub.GetUser(greeter_pb2.GetUserRequest(user_id=-5))
        except grpc.RpcError as e:
            print_rpc_error(e)

        # ── 5. DEADLINE_EXCEEDED ──────────────────────────────────────────
        print("\n5. SayHello with impossibly tight deadline (expect DEADLINE_EXCEEDED):")
        try:
            stub.SayHello(
                greeter_pb2.HelloRequest(name="Timeout"),
                timeout=0.000001,
            )
        except grpc.RpcError as e:
            print_rpc_error(e)

        # ── 6. Successful GetUser (confirm errors don't break the channel) ─
        print("\n6. GetUser (valid) after all the errors above:")
        user = stub.GetUser(greeter_pb2.GetUserRequest(user_id=1))
        print(f"   id={user.id}  name={user.name!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 05 — Error Handling & Metadata")
    print("=" * 60)

    server = make_server()
    server.start()
    time.sleep(0.1)

    try:
        run_client()
    finally:
        server.stop(grace=0)


if __name__ == "__main__":
    main()
