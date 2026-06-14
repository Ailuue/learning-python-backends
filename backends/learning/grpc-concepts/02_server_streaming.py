"""
Concept 02 — Server Streaming RPC

The client sends ONE request. The server sends MANY responses over time,
keeping the connection open until it's done (or the client cancels).

  Client                          Server
    │── SubscribeRequest ────────>│
    │<── PriceUpdate (tick 1) ────│
    │<── PriceUpdate (tick 2) ────│
    │<── PriceUpdate (tick 3) ────│
    │<─────────── EOF ────────────│

Real-world uses:
  - Live price/metric feeds (stocks, sensors, dashboards)
  - Tailing logs
  - Streaming large result sets that don't fit in one message
  - Progress updates for a long-running server operation

The server method uses `yield` (it's a Python generator).
The client iterates the call result directly with a for loop.

HOW TO RUN:
  ./generate_protos.sh   ← if you haven't yet
  python 02_server_streaming.py
"""

import time
import random
from concurrent import futures

import grpc

import stock_pb2
import stock_pb2_grpc

PORT = 50052


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class StockTickerServicer(stock_pb2_grpc.StockTickerServicer):

    def StreamPrices(self, request, context):
        """
        `yield` makes this a generator — gRPC sends each yielded message
        to the client as soon as it's yielded.
        """
        print(f"  [server] Streaming {request.count} prices for {request.symbol!r}")
        base_price = {"AAPL": 189.50, "GOOG": 175.20, "TSLA": 245.00}.get(
            request.symbol, 100.0
        )

        for i in range(request.count):
            if context.is_active() is False:
                # Client cancelled — stop generating
                print("  [server] Client cancelled, stopping stream.")
                return

            price = round(base_price + random.uniform(-2.0, 2.0), 2)
            timestamp_ms = int(time.time() * 1000)

            yield stock_pb2.PriceUpdate(
                symbol=request.symbol,
                price=price,
                timestamp=timestamp_ms,
            )
            time.sleep(0.2)   # simulate real-time cadence


def make_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    stock_pb2_grpc.add_StockTickerServicer_to_server(StockTickerServicer(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    return server


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def run_client():
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = stock_pb2_grpc.StockTickerStub(channel)

        # ── Normal stream — iterate all responses ─────────────────────────
        print("\n1. Stream 5 AAPL price updates:")
        req = stock_pb2.SubscribeRequest(symbol="AAPL", count=5)
        # The stub call returns an iterator — no data flows until we iterate.
        stream = stub.StreamPrices(req)
        for update in stream:
            print(f"   {update.symbol}  ${update.price:.2f}  ts={update.timestamp}")

        # ── Early cancellation ────────────────────────────────────────────
        # .cancel() closes the stream from the client side.
        # The server sees context.is_active() → False on its next check.
        print("\n2. Stream 10 GOOG updates but cancel after 3:")
        req2 = stock_pb2.SubscribeRequest(symbol="GOOG", count=10)
        stream2 = stub.StreamPrices(req2)
        received = 0
        for update in stream2:
            print(f"   {update.symbol}  ${update.price:.2f}")
            received += 1
            if received == 3:
                stream2.cancel()
                print("   (cancelled by client)")
                break

        # ── Stream with deadline ──────────────────────────────────────────
        # If the server is too slow, the client times out.
        print("\n3. Stream with a 0.5s timeout (expect DEADLINE_EXCEEDED):")
        req3 = stock_pb2.SubscribeRequest(symbol="TSLA", count=100)
        try:
            for update in stub.StreamPrices(req3, timeout=0.5):
                print(f"   {update.symbol}  ${update.price:.2f}")
        except grpc.RpcError as e:
            print(f"   Timed out: {e.code()}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 02 — Server Streaming RPC")
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
