#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""lite3_description — static TF primitive for Lite3 quadruped.

Publishes the Lite3 URDF TF tree (base_link → TORSO → limbs + sensor
mounts) plus /joint_states via robot_state_publisher +
joint_state_publisher.  Consumers (SLAM, nav, rtabmap) discover frames
through the global ROS 2 /tf + /tf_static side-channels.

Because TF is a ROS 2 side-channel (every tf2-aware node joins /tf +
/tf_static automatically), this primitive declares no atlas-routed
contracts (capabilities: []).  rbnx boot auto-promotes us to ACTIVE
immediately after registration — no Driver(CMD_INIT) handshake.

Lifecycle:
    on_init     — resolve URDF path from config/env, spawn
                  robot_state_publisher + joint_state_publisher
                  via ros2 launch subprocess.
    on_shutdown — kill ros2 launch subprocess group.
"""
from __future__ import annotations

import logging
import os
import signal
import subprocess
from pathlib import Path

from robonix_api import Primitive, Ok, Err

logging.basicConfig(
    level=os.environ.get("LITE3_DESC_LOG_LEVEL", "INFO"),
    format="[lite3_desc] %(message)s",
)
log = logging.getLogger("lite3_description")

lite3_description = Primitive(id="lite3_description", namespace="robonix/primitive/tf")

_pkg_root: Path = Path(__file__).resolve().parent.parent
_launch_proc: subprocess.Popen | None = None

# Default URDF path (relative to package root).  Override via
# LITE3_URDF_PATH env var or the manifest config block.
_DEFAULT_URDF = "deep_robotics_model/Lite3/Lite3_urdf/urdf/Lite3.urdf"


# ── ros2 launch subprocess management ────────────────────────────────────
def _spawn_launch(urdf_rel: str) -> None:
    """Spawn ``ros2 launch display.launch.py`` in its own process group.

    The launch file runs robot_state_publisher (URDF → /tf, /tf_static)
    and joint_state_publisher (/joint_states).
    """
    global _launch_proc

    launch_file = str(_pkg_root / "launch" / "display.launch.py")
    if not os.path.isfile(launch_file):
        raise RuntimeError(f"launch file missing: {launch_file}")

    log_path = _pkg_root / "rbnx-build" / "data" / "display.launch.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(log_path, "ab", buffering=0)

    log.info("spawning ros2 launch %s urdf_path=%s → %s",
             launch_file, urdf_rel, log_path)
    _launch_proc = subprocess.Popen(
        ["ros2", "launch", launch_file, f"urdf_path:={urdf_rel}"],
        stdout=log_fh, stderr=log_fh,
        start_new_session=True,
    )


def _kill_launch() -> None:
    """Kill the ros2 launch subprocess group (SIGTERM → SIGKILL fallback).

    Same pattern as lite3_quadruped._kill_transfer and
    mid360_lidar._kill_livox.
    """
    p = _launch_proc
    if p is None or p.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        p.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        log.warning("ros2 launch did not exit after SIGTERM; sending SIGKILL")
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


# ── lifecycle handlers ──────────────────────────────────────────────────
#
# NOTE: lite3_description has no contracts (declared as static TF side-channel),
# so atlas auto-promotes it to ACTIVE with "(no driver)".  @on_init is NOT
# called.  The actual spawn happens in __main__ below, before Primitive.run().
# @on_init is kept as a forward-compat stub for when a driver is added later.

@lite3_description.on_init
def init(cfg):
    """(Reserved) Spawn ros2 launch when a driver becomes available."""
    urdf_rel = cfg.get("urdf_path") or os.environ.get("LITE3_URDF_PATH", _DEFAULT_URDF)
    urdf_path = Path(urdf_rel)
    if not urdf_path.is_absolute():
        urdf_path = _pkg_root / urdf_path

    if urdf_path.is_file():
        log.info("URDF: %s (%d bytes)", urdf_path, urdf_path.stat().st_size)
        try:
            _spawn_launch(str(urdf_rel))
        except Exception as e:
            return Err(f"spawn ros2 launch failed: {e}")
    else:
        log.error("URDF file not found: %s — TF tree will be empty", urdf_path)

    return Ok()


@lite3_description.on_shutdown
def shutdown():
    """Kill ros2 launch subprocess on primitive shutdown."""
    _kill_launch()
    return Ok()


if __name__ == "__main__":
    # Spawn ros2 launch BEFORE Primitive.run() — because this primitive
    # has no driver, @on_init never fires.  We spawn directly so
    # robot_state_publisher + joint_state_publisher are alive by the
    # time atlas registers us.
    urdf_rel = os.environ.get("LITE3_URDF_PATH", _DEFAULT_URDF)
    urdf_path = Path(urdf_rel)
    if not urdf_path.is_absolute():
        urdf_path = _pkg_root / urdf_path

    if urdf_path.is_file():
        log.info("URDF: %s (%d bytes)", urdf_path, urdf_path.stat().st_size)
        _spawn_launch(str(urdf_rel))
    else:
        log.error("URDF file not found: %s — TF tree will be empty", urdf_path)

    lite3_description.run()
