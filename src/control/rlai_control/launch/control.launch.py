"""
rlai_control/launch/control.launch.py

Starts the full ros2_control stack for rbot:
  1. joint_state_broadcaster — publishes /joint_states from ros2_control
  2. diff_drive_controller   — drives wheels, publishes /wheel_odom
  3. velocity_smoother       — smooths /cmd_vel → /diff_drive_controller/cmd_vel
  4. lifecycle_manager       — auto-activates velocity_smoother

Prerequisites (provided by Gazebo + Phase 3):
  - Gazebo must already be running with the robot spawned.
  - The gz_ros2_control/GazeboSimSystem plugin starts controller_manager
    automatically when the robot model loads; this launch file only spawns
    controllers into that already-running manager.

Topic routing after this launch:
  teleop/nav2 → /cmd_vel → velocity_smoother → /diff_drive_controller/cmd_vel
  diff_drive_controller  →  /wheel_odom       (nav_msgs/Odometry, 50 Hz)
  joint_state_broadcaster →  /joint_states   (sensor_msgs/JointState, 50 Hz)

Usage:
  ros2 launch rlai_control control.launch.py
  ros2 launch rlai_control control.launch.py use_sim_time:=false  # real robot
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare("rlai_control")

    controllers_yaml = PathJoinSubstitution([pkg, "config", "controllers.yaml"])
    smoother_yaml = PathJoinSubstitution([pkg, "config", "velocity_smoother.yaml"])

    # Launch arguments
    declared_args = [
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use simulation (Gazebo) clock",
        ),
    ]

    # Load before diff_drive_controller so /joint_states is available for wheel positions.
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        name="joint_state_broadcaster_spawner",
        arguments=[
            "joint_state_broadcaster",
            "--param-file", controllers_yaml,
        ],
        output="screen",
    )

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        name="diff_drive_controller_spawner",
        arguments=[
            "diff_drive_controller",
            "--param-file", controllers_yaml,
        ],
        output="screen",
    )

    # Smooth /cmd_vel before forwarding TwistStamped commands to diff_drive_controller.
    velocity_smoother = Node(
        package="nav2_velocity_smoother",
        executable="velocity_smoother",
        name="velocity_smoother",
        parameters=[
            smoother_yaml,
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
        remappings=[
            ("cmd_vel",          "/cmd_vel"),
            ("cmd_vel_smoothed", "/diff_drive_controller/cmd_vel"),
        ],
        output="screen",
    )

    # Auto-configures and activates the velocity_smoother lifecycle node.
    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_control",
        output="screen",
        parameters=[{
            "autostart": True,
            "node_names": ["velocity_smoother"],
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }],
    )

    # Delay lifecycle_manager 3 s to give velocity_smoother time to fully initialize
    # before the manager attempts the configure transition.
    lifecycle_manager_delayed = TimerAction(
        period=3.0,
        actions=[lifecycle_manager],
    )

    return LaunchDescription(
        declared_args + [
            joint_state_broadcaster_spawner,
            diff_drive_spawner,
            velocity_smoother,
            lifecycle_manager_delayed,
        ]
    )
