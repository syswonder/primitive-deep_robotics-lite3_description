#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# lite3_description runtime — start the static TF primitive.
#
# rbnx boot sends Driver(CMD_INIT, config_json) → @cap.on_init spawns
# ros2 launch display.launch.py (robot_state_publisher + joint_state_publisher).
set -euo pipefail

PKG="$(cd "$(dirname "$0")/.." && pwd)"
# ROS setup.bash may reference unset variables; disable nounset temporarily.
set +u
if [ -f "/opt/ros/humble/setup.bash" ]; then
  source /opt/ros/humble/setup.bash
fi
set -u

cleanup() {
  kill -- "-$$" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

export PYTHONPATH="$PKG:$PYTHONPATH"
export PYTHONPATH="/home/jetson/cxk/robonix/pylib/robonix-api:$PYTHONPATH"

exec python3 -m lite3_description.main
