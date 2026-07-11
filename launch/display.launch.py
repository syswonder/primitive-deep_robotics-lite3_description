#!/usr/bin/env python3
"""Launch robot_state_publisher + joint_state_publisher for Lite3.

References the display.launch.py pattern from ranger_description:
  - robot_state_publisher: publishes URDF TF tree (base_link → TORSO → limbs + sensors)
  - joint_state_publisher: publishes /joint_states for revolute joints

The URDF is a plain XML file (not xacro). We read it at launch time and
pass the content as the robot_description parameter.
"""
import os
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
import launch_ros.actions


def _launch_setup(context, *args, **kwargs):
    """Read URDF and create nodes."""
    urdf_path = LaunchConfiguration("urdf_path").perform(context)

    # If relative, resolve against this package's root
    if not os.path.isabs(urdf_path):
        pkg_root = Path(__file__).resolve().parent.parent
        urdf_path = str(pkg_root / urdf_path)

    urdf_text = Path(urdf_path).read_text(encoding="utf-8")

    robot_state_publisher_node = launch_ros.actions.Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[{"robot_description": urdf_text}],
        output="screen",
    )

    joint_state_publisher_node = launch_ros.actions.Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        parameters=[{"use_sim_time": False}],
        output="screen",
    )

    return [robot_state_publisher_node, joint_state_publisher_node]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "urdf_path",
            default_value="deep_robotics_model/Lite3/Lite3_urdf/urdf/Lite3.urdf",
            description="Path to Lite3 URDF file (relative to package root or absolute)",
        ),
        OpaqueFunction(function=_launch_setup),
    ])
