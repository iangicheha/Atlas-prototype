"""
lidar_processing.launch.py

Starts the rlai point-cloud filter node that converts
  /lidar_3d/points_raw  →  /lidar_3d/points
(VoxelGrid downsample + height PassThrough filter)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('rlai_lidar_processing')

    use_sim_time = LaunchConfiguration('use_sim_time')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock'),

        Node(
            package='rlai_lidar_processing',
            executable='pointcloud_filter_node',
            name='pointcloud_filter',
            parameters=[
                PathJoinSubstitution([pkg, 'config', 'pointcloud_filter.yaml']),
                {'use_sim_time': use_sim_time},
            ],
            output='screen',
            emulate_tty=True,
        ),
    ])
