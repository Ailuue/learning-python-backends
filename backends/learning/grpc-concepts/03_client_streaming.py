"""
Concept 03 — Client Streaming RPC

The client sends MANY requests. The server reads them all, then sends ONE response.

  Client                          Server
    │── Chunk (part 1) ──────────>│
    │── Chunk (part 2) ──────────>│
    │── Chunk (part 3) ──────────>│  (accumulates chunks)
    │── EOF ─────────────────────>│
    │<── UploadResult ────────────│

Real-world uses:
  - File / binary upload in chunks
  - Batch inserts (stream rows, get a summary count)
  - Collecting sensor readings before computing an aggregate
  - Audio/video upload pipelines

The client passes a *generator* to the stub call. gRPC reads that generator
in a background thread, streaming each message to the server.
The stub call blocks until the server sends its single response.

HOW TO RUN:
  ./generate_protos.sh   ← if you haven't yet
  python 03_client_streaming.py
"""

import time
import threading
from concurrent import futures

import grpc

import upload_pb2
import upload_pb2_grpc

PORT = 50053
CHUNK_SIZE = 64 * 1024   # 64 KB per chunk


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

class FileUploadServicer(upload_pb2_grpc.FileUploadServicer):

    def UploadFile(self, request_iterator, context):
        """
        `request_iterator` is an iterator of Chunk messages.
        We iterate it to completion, then return a single UploadResult.
        """
        total_chunks = 0
        total_bytes = 0
        filename = None

        for chunk in request_iterator:
            if filename is None:
                filename = chunk.filename
            total_chunks += 1
            total_bytes += len(chunk.data)
            print(f"  [server] Received chunk {chunk.chunk_index}: {len(chunk.data)} bytes")

        print(f"  [server] Upload complete: {total_chunks} chunks, {total_bytes} bytes")
        return upload_pb2.UploadResult(
            filename=filename or "unknown",
            total_chunks=total_chunks,
            total_bytes=total_bytes,
            status="ok",
        )


def make_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    upload_pb2_grpc.add_FileUploadServicer_to_server(FileUploadServicer(), server)
    server.add_insecure_port(f"[::]:{PORT}")
    return server


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

def chunk_generator(filename: str, data: bytes, chunk_size: int):
    """
    Yields Chunk messages from raw bytes.
    This generator is passed directly to the stub — gRPC streams it to the server.
    """
    index = 0
    for offset in range(0, len(data), chunk_size):
        yield upload_pb2.Chunk(
            filename=filename,
            data=data[offset : offset + chunk_size],
            chunk_index=index,
        )
        index += 1
        time.sleep(0.05)   # simulate real upload latency


def run_client():
    with grpc.insecure_channel(f"localhost:{PORT}") as channel:
        stub = upload_pb2_grpc.FileUploadStub(channel)

        # ── Small file (single chunk) ─────────────────────────────────────
        print("\n1. Upload a small file (fits in one chunk):")
        small_data = b"Hello, gRPC!" * 10
        result = stub.UploadFile(
            chunk_generator("hello.txt", small_data, CHUNK_SIZE)
        )
        print(f"   filename={result.filename}  chunks={result.total_chunks}"
              f"  bytes={result.total_bytes}  status={result.status!r}")

        # ── Larger file (multiple chunks) ─────────────────────────────────
        print("\n2. Upload a larger file (3 chunks of 64 KB each):")
        large_data = b"x" * (3 * CHUNK_SIZE)
        result2 = stub.UploadFile(
            chunk_generator("bigfile.bin", large_data, CHUNK_SIZE)
        )
        print(f"   filename={result2.filename}  chunks={result2.total_chunks}"
              f"  bytes={result2.total_bytes}  status={result2.status!r}")

        # ── Empty stream ──────────────────────────────────────────────────
        print("\n3. Upload nothing (empty generator — edge case):")
        def empty():
            return iter([])
        result3 = stub.UploadFile(empty())
        print(f"   chunks={result3.total_chunks}  bytes={result3.total_bytes}"
              f"  status={result3.status!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 03 — Client Streaming RPC")
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
