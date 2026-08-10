#!/usr/bin/env bash
# Run this once after `pip install -r requirements.txt`.
# Compiles all .proto files and outputs *_pb2.py + *_pb2_grpc.py + *_pb2.pyi
# into the current directory (alongside the concept files).
#
# --pyi_out matters for the editor: the generated *_pb2.py builds its message
# classes at runtime via _builder, so without the .pyi stubs Pylance reports
# every HelloRequest / PriceUpdate / Chunk as an unknown module attribute.
set -e
cd "$(dirname "$0")"

python -m grpc_tools.protoc \
  --proto_path=proto \
  --python_out=. \
  --pyi_out=. \
  --grpc_python_out=. \
  proto/greeter.proto \
  proto/stock.proto \
  proto/upload.proto \
  proto/chat.proto

echo "Generated:"
ls -1 *_pb2*.py *_pb2.pyi
