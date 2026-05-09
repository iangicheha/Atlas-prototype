"""
camera_processing.launch.py

Starts the camera perception pipeline as a single composable node container.

Pipeline:
  ┌─────────────────────────────────────────────────────────────────┐
  │  camera_pipeline_container  (rclcpp_components)                 │
  │                                                                 │
  │  image_proc::RectifyNode  (ns: stereo/left)                     │
  │    /stereo/left/image_raw  →  /stereo/left/image_rect           │
  │                                                                 │
  │  image_proc::RectifyNode  (ns: stereo/right)                    │
  │    /stereo/right/image_raw →  /stereo/right/image_rect          │
  │                                                                 │
  │  stereo_image_proc::DisparityNode  (ns: stereo)                 │
  │    left + right rect  →  /stereo/disparity                      │
  │                                                                 │
  │  stereo_image_proc::PointCloudNode  (ns: stereo)                │
  │    disparity + rect   →  /stereo/points2                        │
  │                                                                 │
  │  depth_image_proc::PointCloudXyzNode  (ns: depth_camera)        │
  │    /depth_camera/depth  →  /depth_camera/points                 │
  └─────────────────────────────────────────────────────────────────┘
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer, LoadComposableNodes
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('rlai_camera_processing')

    use_sim_time = LaunchConfiguration('use_sim_time')
    depth_camera_enabled = LaunchConfiguration('depth_camera_enabled')
    stereo_camera_enabled = LaunchConfiguration('stereo_camera_enabled')
    stereo_params = PathJoinSubstitution([pkg, 'config', 'stereo_params.yaml'])

    stereo_nodes = [
        ComposableNode(
            package='image_proc',
            plugin='image_proc::RectifyNode',
            name='rectify_left',
            namespace='stereo/left',
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[
                ('image',        '/stereo/left/image_raw'),
                ('camera_info',  '/stereo/left/camera_info'),
                ('image_rect',   '/stereo/left/image_rect'),
            ],
        ),
        ComposableNode(
            package='image_proc',
            plugin='image_proc::RectifyNode',
            name='rectify_right',
            namespace='stereo/right',
            parameters=[{'use_sim_time': use_sim_time}],
            remappings=[
                ('image',        '/stereo/right/image_raw'),
                ('camera_info',  '/stereo/right/camera_info'),
                ('image_rect',   '/stereo/right/image_rect'),
            ],
        ),
        ComposableNode(
            package='stereo_image_proc',
            plugin='stereo_image_proc::DisparityNode',
            name='disparity',
            namespace='stereo',
            parameters=[
                stereo_params,
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('left/image_rect_color',  '/stereo/left/image_rect'),
                ('left/camera_info',       '/stereo/left/camera_info'),
                ('right/image_rect',       '/stereo/right/image_rect'),
                ('right/camera_info',      '/stereo/right/camera_info'),
                ('disparity',              '/stereo/disparity'),
            ],
        ),
        ComposableNode(
            package='stereo_image_proc',
            plugin='stereo_image_proc::PointCloudNode',
            name='pointcloud',
            namespace='stereo',
            parameters=[
                stereo_params,
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('left/image_rect_color',  '/stereo/left/image_rect'),
                ('left/camera_info',       '/stereo/left/camera_info'),
                ('right/camera_info',      '/stereo/right/camera_info'),
                ('disparity',              '/stereo/disparity'),
                ('points2',                '/stereo/points2'),
            ],
        ),
    ]

    depth_nodes = [
        ComposableNode(
            package='depth_image_proc',
            plugin='depth_image_proc::PointCloudXyzNode',
            name='depth_to_pointcloud',
            namespace='depth_camera',
            parameters=[
                stereo_params,
                {'use_sim_time': use_sim_time},
            ],
            remappings=[
                ('image_rect',   '/depth_camera/depth'),
                ('camera_info',  '/depth_camera/camera_info'),
                ('points',       '/depth_camera/points'),
            ],
        ),
    ]

    # Single container — all camera nodes share intra-process comms
    camera_container = ComposableNodeContainer(
        name='camera_pipeline_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[],
        output='screen',
    )

    load_stereo_nodes = LoadComposableNodes(
        target_container='camera_pipeline_container',
        composable_node_descriptions=stereo_nodes,
        condition=IfCondition(stereo_camera_enabled),
    )

    load_depth_nodes = LoadComposableNodes(
        target_container='camera_pipeline_container',
        composable_node_descriptions=depth_nodes,
        condition=IfCondition(depth_camera_enabled),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock'),
        DeclareLaunchArgument(
            'depth_camera_enabled',
            default_value='true',
            description='Start depth image point-cloud processing'),
        DeclareLaunchArgument(
            'stereo_camera_enabled',
            default_value='false',
            description='Start stereo rectification, disparity, and point-cloud processing'),

        camera_container,
        load_stereo_nodes,
        load_depth_nodes,
    ])
