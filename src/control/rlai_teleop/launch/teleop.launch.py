"""
rlai_teleop/launch/teleop.launch.py

Launches the full teleoperation stack for rbot:
  1. joy_linux_node     — reads /dev/input/jsX and publishes sensor_msgs/Joy
  2. teleop_twist_joy   — converts Joy to TwistStamped on /cmd_vel
  3. estop_node         — provides /e_stop toggle service and publishes zero
                          velocity commands while engaged

Topic routing after this launch:
  Joystick HW -> joy_linux_node -> /joy -> teleop_twist_joy -> /cmd_vel -> velocity_smoother
  ros2 service call /e_stop -> estop_node -> /cmd_vel (zero override while active)

Prerequisites:
  - control.launch.py must already be running so velocity_smoother consumes /cmd_vel.
  - A joystick must be present at /dev/input/js0 (or change device_id).

Usage:
  ros2 launch rlai_teleop teleop.launch.py
  ros2 launch rlai_teleop teleop.launch.py use_sim_time:=false  # real robot
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('rlai_teleop')
    joy_cfg = PathJoinSubstitution([pkg, 'config', 'joystick.yaml'])

    # Launch arguments
    declared_args = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock',
        ),
    ]

    # Reads the physical or virtual joystick and publishes sensor_msgs/Joy.
    joy_node = Node(
        package='joy_linux',
        executable='joy_linux_node',
        name='joy_linux_node',
        parameters=[
            joy_cfg,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
        output='screen',
    )

    # Converts Joy → Twist.  Enable button (L1) must be held for motion.
    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy',
        parameters=[
            joy_cfg,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
        remappings=[
            ('cmd_vel', 'cmd_vel'),
        ],
        output='screen',
    )

    # Toggle /e_stop service; overrides /cmd_vel with zeros when engaged.
    estop_node = Node(
        package='rlai_teleop',
        executable='estop_node',
        name='estop_node',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
        output='screen',
    )

    return LaunchDescription(
        declared_args + [
            joy_node,
            teleop_node,
            estop_node,
        ]
    )
