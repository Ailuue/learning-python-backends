"""
Concept 06 — Interceptors (Middleware)

Interceptors are middleware that wrap every RPC on a channel or server.
They let you inject cross-cutting concerns — logging, auth, rate-limiting,
tracing, metrics — without touching the business logic of each RPC method.

gRPC has interceptors on both sides:

  SERVER interceptors: wrap incoming RPCs before they reach the servicer.
    - Inspect/modify request metadata
    - Abort the call early (e.g. auth failure)
    - Log call duration

  CLIENT interceptors: wrap outgoing RPCs before they leave the channel.
    - Inject auth headers automatically
    - Add distributed-tracing IDs
    - Retry on specific errors

Both are passed to the server/channel constructor — they compose in order.

Python's server interceptor API:
  intercept_service(continuation, handler_call_details)
    - handler_call_details.method              → "/PackageName/MethodName"
    - handler_call_details.invocation_metadata → client-sent metadata
    - continuation(handler_call_details)        → calls the next interceptor (or the handler)
    - return value is a grpc.RpcMethodHandler  → can be replaced to abort early

HOW TO RUN:
  ./generate_protos.sh   ← if you haven't yet
  python 06_interceptors.py
"""

import time
import logging
from concurrent import futures

import grpc

import greeter_pb2
import greeter_pb2_grpc

PORT = 50056
VALID_TOKEN = "secret-token-abc"

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Interceptor 1 — Server-side logging
# ---------------------------------------------------------------------------

class LoggingInterceptor(grpc.ServerInterceptor):
    """Logs the method name and duration of every RPC."""

    def intercept_service(self, continuation, handler_call_details):
        method = handler_call_details.method   # e.g. "/Greeter/SayHello"
        handler = continuation(handler_call_details)

        if handler is None:
            return handler

        # Wrap the actual handler function to add timing
        original_fn = (
            handler.unary_unary
            or handler.unary_stream
            or handler.stream_unary
            or handler.stream_stream
        )
        if original_fn is None:
            return handler

        def timed_fn(request_or_iterator, context):
            start = time.perf_counter()
            try:
                result = original_fn(request_or_iterator, context)
                elapsed = (time.perf_counter() - start) * 1000
                log.info(f"  [log] {method}  OK  {elapsed:.1f}ms")
                return result
            except Exception as exc:
                elapsed = (time.perf_counter() - start) * 1000
                log.info(f"  [log] {method}  ERROR  {elapsed:.1f}ms  {exc}")
                raise

        # Rebuild the handler with the wrapped function
        return handler._replace(unary_unary=timed_fn)


# ---------------------------------------------------------------------------
# Interceptor 2 — Server-side auth token check
# ---------------------------------------------------------------------------

class AuthInterceptor(grpc.ServerInterceptor):
    """
    Checks that the client sends an 'authorization' metadata key matching
    VALID_TOKEN. Aborts with UNAUTHENTICATED if it's missing or wrong.
    """

    def __init__(self, token: str):
        self._token = token

        # Pre-build an abort handler to return on auth failure
        def unauthenticated(request, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or missing token")

        self._abort_handler = grpc.unary_unary_rpc_method_handler(unauthenticated)

    def intercept_service(self, continuation, handler_call_details):
        meta = dict(handler_call_details.invocation_metadata)
        token = meta.get("authorization", "")
        if token != self._token:
            log.info(f"  [auth] REJECTED  token={token!r}")
            return self._abort_handler
        log.info(f"  [auth] ACCEPTED  token={token!r}")
        return continuation(handler_call_details)


# ---------------------------------------------------------------------------
# Interceptor 3 — Client-side token injection
# ---------------------------------------------------------------------------

class TokenInjectorInterceptor(grpc.UnaryUnaryClientInterceptor):
    """
    Automatically adds the 'authorization' header to every outgoing call.
    The client code never has to pass metadata= manually.
    """

    def __init__(self, token: str):
        self._token = token

    def intercept_unary_unary(self, continuation, client_call_details, request):
        # Merge the token into existing metadata (if any)
        existing = list(client_call_details.metadata or [])
        existing.append(("authorization", self._token))
        new_details = client_call_details._replace(metadata=existing)
        return continuation(new_details, request)


# ---------------------------------------------------------------------------
# Servicer
# ---------------------------------------------------------------------------

class GreeterServicer(greeter_pb2_grpc.GreeterServicer):

    def SayHello(self, request, context):
        return greeter_pb2.HelloReply(message=f"Hello, {request.name}!")

    def GetUser(self, request, context):
        users = {
            1: greeter_pb2.User(id=1, name="Alex", email="alex@example.com"),
        }
        if request.user_id not in users:
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.user_id} not found")
        return users[request.user_id]


def make_server():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=4),
        # Interceptors are applied outermost-first (auth runs before logging)
        interceptors=[AuthInterceptor(VALID_TOKEN), LoggingInterceptor()],
    )
    greeter_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    return server


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def run_client():
    # ── 1. No auth token — expect UNAUTHENTICATED ─────────────────────────
    print("\n1. Call without auth token (expect UNAUTHENTICATED):")
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = greeter_pb2_grpc.GreeterStub(channel)
        try:
            stub.SayHello(greeter_pb2.HelloRequest(name="Alex"))
        except grpc.RpcError as e:
            print(f"   {e.code()}: {e.details()}")

    # ── 2. Wrong token ────────────────────────────────────────────────────
    print("\n2. Call with wrong token (expect UNAUTHENTICATED):")
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = greeter_pb2_grpc.GreeterStub(channel)
        try:
            stub.SayHello(
                greeter_pb2.HelloRequest(name="Alex"),
                metadata=[("authorization", "wrong-token")],
            )
        except grpc.RpcError as e:
            print(f"   {e.code()}: {e.details()}")

    # ── 3. Correct token passed manually ─────────────────────────────────
    print("\n3. Call with correct token (manually):")
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = greeter_pb2_grpc.GreeterStub(channel)
        reply = stub.SayHello(
            greeter_pb2.HelloRequest(name="Alex"),
            metadata=[("authorization", VALID_TOKEN)],
        )
        print(f"   {reply.message!r}")

    # ── 4. Client interceptor injects token automatically ─────────────────
    print("\n4. Using client interceptor — token injected automatically:")
    with grpc.intercept_channel(
        grpc.insecure_channel(f"localhost:{PORT}"),
        TokenInjectorInterceptor(VALID_TOKEN),
    ) as channel:
        stub = greeter_pb2_grpc.GreeterStub(channel)
        # No metadata= needed — the interceptor adds it behind the scenes
        reply = stub.SayHello(greeter_pb2.HelloRequest(name="Dana"))
        print(f"   {reply.message!r}")

        user = stub.GetUser(greeter_pb2.GetUserRequest(user_id=1))
        print(f"   GetUser → id={user.id}  name={user.name!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 06 — Interceptors")
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
