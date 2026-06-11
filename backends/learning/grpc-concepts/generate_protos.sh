#!/usr/bin/env bash
# Run this once after `pip install -r requirements.txt`.
# Compiles all .proto files and outputs *_pb2.py + *_pb2_grpc.py
# into the current directory (alongside the concept files).
set -e
cd "$(dirname "$0")"

python -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=. \
  --grpc_python_out=. \
  proto/greeter.proto \
  proto/stock.proto \
  proto/upload.proto \
  proto/chat.proto

echo "Generated:"
ls -1 *_pb2*.py
