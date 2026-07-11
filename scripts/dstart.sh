#!/usr/bin/env bash
# Debug: manually publish static TF transforms for development/testing.
# The production version runs inside Driver(CMD_INIT) via main.py.
set -euo pipefail
PKG="$(cd "$(dirname "$0")/.." && pwd)"

ROS_DISTRO="${ROS_DISTRO:-humble}"
set +u; source "/opt/ros/${ROS_DISTRO}/setup.bash"; set -u

# Publish static TF: base_link → unilidar_lidar (sensor mounting)
ros2 run tf2_ros static_transform_publisher \
  --x 0 --y 0 --z 0 \
  --roll 0 --pitch 0 --yaw 0 \
  --frame-id base_link \
  --child-frame-id unilidar_lidar