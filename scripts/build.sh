#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# Build phase: rbnx codegen ONLY.  The generated atlas_pb2 + atlas_pb2_grpc
# Python stubs are needed by robonix_api.Primitive (which main.py uses) to
# register on atlas, heartbeat, and serve the Driver gRPC lifecycle.
# The actual TF publishing is done by ``ros2 launch display.launch.py``
# at runtime — this package vendors no compiled source.
set -euo pipefail
PKG="${RBNX_PACKAGE_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$PKG"
CLEAN="${RBNX_BUILD_CLEAN:-}"

if [[ "$CLEAN" == "1" ]]; then
    echo "[lite3_description/build] clean: removing rbnx-build/"
    rm -rf rbnx-build
fi
mkdir -p rbnx-build/data

FLAGS=(--out-dir "$PKG/rbnx-build/codegen")
[[ "$CLEAN" == "1" ]] && FLAGS+=(--clean)
echo "[lite3_description/build] rbnx codegen ${FLAGS[*]}"
rbnx codegen -p "$PKG" "${FLAGS[@]}"

touch "$PKG/rbnx-build/.rbnx-built"
echo "[lite3_description/build] done."
