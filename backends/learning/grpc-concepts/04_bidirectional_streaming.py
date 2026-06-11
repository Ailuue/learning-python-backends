"""
Concept 04 — Bidirectional Streaming RPC

Both sides send multiple messages independently, over a single persistent
connection. Neither side has to wait for the other before sending.

  Client                          Server
    │── ChatMessage("hi") ───────>│
    │<── ChatMessage("[echo] hi") ─│
    │── ChatMessage("how are u") >│
    │<── ChatMessage("[echo] …") ─│
    │── EOF ─────────────────────>│
    │<── EOF ─────────────────────│

Real-world uses:
  - Chat / messaging
  - Real-time collaborative editing
  - Two-way sensor telemetry
  - Multiplayer game state sync

How gRPC handles the two directions:
  Server side:
    - Receives `request_iterator` (iterating it reads from the client)
    - Uses `yield` to write to the client
    - The method ends (falls off the last yield) to signal EOF to client

  Client side:
    - Passes a generator as the request (gRPC reads it in a background thread)
    - The stub call returns a response iterator
    - The client iterates responses in its own loop

In this demo, the server echoes every client message back with an "[echo]" prefix.
The client sends 5 messages, 0.3s apart.

HOW TO RUN:
  ./generate_protos.sh   ← if you haven't yet
  python 04_bidirectional_streaming.py
"""

import time
import threading
from concurrent import futures

import grpc

import chat_pb2
import chat_pb2_grpc

PORT = 50054


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class ChatServicer(chat_pb2_grpc.ChatServicer):

    def Connect(self, request_iterator, context):
        """
        For every message the client sends, yield an echo response.
        When the client stops sending (request_iterator is exhausted),
        this generator also ends, signalling EOF to the client.
        """
        for msg in request_iterator:
            print(f"  [server] received from {msg.user!r}: {msg.text!r}")
            yield chat_pb2.ChatMessage(
                user="server",
                text=f"[echo] {msg.text}",
                timestamp=int(time.time() * 1000),
            )


def make_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    chat_pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    return server


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

MESSAGES = [
    "hello there",
    "how are you?",
    "what's the weather like?",
    "tell me a joke",
    "goodbye!",
]


def message_generator(user: str, messages: list):
    """
    Yields outbound ChatMessages with a small delay between each.
    gRPC streams these to the server in a background thread while the
    client's main thread is iterating the response iterator.
    """
    for text in messages:
        print(f"  [client] sending: {text!r}")
        yield chat_pb2.ChatMessage(
            user=user,
            text=text,
            timestamp=int(time.time() * 1000),
        )
        time.sleep(0.3)


def run_client():
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = chat_pb2_grpc.ChatStub(channel)

        # ── Full bidirectional exchange ───────────────────────────────────
        print("\n1. Full bidirectional chat (5 messages, each echoed back):")
        response_stream = stub.Connect(message_generator("alex", MESSAGES))

        # Iterating response_stream reads from the server.
        # Meanwhile, message_generator() is running in a gRPC background thread,
        # sending messages to the server concurrently.
        for reply in response_stream:
            print(f"  [client] received from {reply.user!r}: {reply.text!r}")

        # ── Early client disconnect ────────────────────────────────────────
        print("\n2. Client disconnects after receiving 2 replies:")

        def short_generator():
            for text in ["msg1", "msg2", "msg3", "msg4"]:
                print(f"  [client] sending: {text!r}")
                yield chat_pb2.ChatMessage(
                    user="alex", text=text,
                    timestamp=int(time.time() * 1000),
                )
                time.sleep(0.2)

        stream2 = stub.Connect(short_generator())
        received = 0
        for reply in stream2:
            print(f"  [client] received: {reply.text!r}")
            received += 1
            if received == 2:
                stream2.cancel()
                print("  [client] cancelled stream")
                break


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 04 — Bidirectional Streaming RPC")
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
