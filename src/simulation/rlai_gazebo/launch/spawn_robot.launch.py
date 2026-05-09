"""Spawn an rbot model into a running Gazebo world."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import Node


def generate_launch_description():
    """Create the robot spawn launch description."""
    declared_args = [
        DeclareLaunchArgument('robot_name', default_value='rlai_bot',
                              description='Model name inside Gazebo'),
        DeclareLaunchArgument('description_topic', default_value='robot_description',
                              description='ROS topic carrying the URDF string'),
        DeclareLaunchArgument('x', default_value='0.0',
                              description='Spawn X position [m]'),
        DeclareLaunchArgument('y', default_value='0.0',
                              description='Spawn Y position [m]'),
        DeclareLaunchArgument('z', default_value='0.1',
                              description='Spawn Z position [m]'),
        DeclareLaunchArgument('yaw', default_value='0.0',
                              description='Spawn yaw angle [rad]'),
    ]

    spawn_node = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_robot',
        output='screen',
        arguments=[
            '-topic', LaunchConfiguration('description_topic'),
            '-name', LaunchConfiguration('robot_name'),
            '-x', LaunchConfiguration('x'),
            '-y', LaunchConfiguration('y'),
            '-z', LaunchConfiguration('z'),
            '-Y', LaunchConfiguration('yaw'),
        ],
    )

    return LaunchDescription(declared_args + [spawn_node])
