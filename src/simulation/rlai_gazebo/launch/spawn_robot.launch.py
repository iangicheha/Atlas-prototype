"""
rlai_gazebo/launch/spawn_robot.launch.py

Isolated robot spawn helper.
Use this to re-spawn (or spawn a second robot) without restarting the world.

Requires:
  - A running Gazebo instance  (gz sim already started via gazebo.launch.py)
  - /robot_description already being published  (robot_state_publisher running)

Usage:
  ros2 launch rlai_gazebo spawn_robot.launch.py
  ros2 launch rlai_gazebo spawn_robot.launch.py x:=3.0 y:=-1.0 robot_name:=rlai_bot_2
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    declared_args = [
        DeclareLaunchArgument("robot_name", default_value="rlai_bot",
                              description="Model name inside Gazebo"),
        DeclareLaunchArgument("description_topic", default_value="robot_description",
                              description="ROS topic carrying the URDF string"),
        DeclareLaunchArgument("x",   default_value="0.0",
                              description="Spawn X position [m]"),
        DeclareLaunchArgument("y",   default_value="0.0",
                              description="Spawn Y position [m]"),
        DeclareLaunchArgument("z",   default_value="0.1",
                              description="Spawn Z position [m]"),
        DeclareLaunchArgument("yaw", default_value="0.0",
                              description="Spawn yaw angle [rad]"),
    ]

    spawn_node = Node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_robot",
        output="screen",
        arguments=[
            "-topic", LaunchConfiguration("description_topic"),
            "-name",  LaunchConfiguration("robot_name"),
            "-x",  LaunchConfiguration("x"),
            "-y",  LaunchConfiguration("y"),
            "-z",  LaunchConfiguration("z"),
            "-Y",  LaunchConfiguration("yaw"),
        ],
    )

    return LaunchDescription(declared_args + [spawn_node])
