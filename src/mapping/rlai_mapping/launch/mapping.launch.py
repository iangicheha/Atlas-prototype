"""
rlai_mapping/launch/mapping.launch.py

SLAM Toolbox online-async mapping session for rbot.

What this launches:
  1. async_slam_toolbox_node  — builds occupancy map from /scan,
                                publishes /map and map→odom TF
  2. map_saver_server         — listens for save-map service calls:
       ros2 run nav2_map_server map_saver_cli -f /path/to/map
  3. lifecycle_manager        — auto-configures + activates map_saver_server
  4. rviz2 (optional)         — overhead SLAM visualisation

Prerequisites (must be running before this launch file):
  - Gazebo + robot_state_publisher          (rlai_gazebo/gazebo.launch.py)
  - ros2_control + velocity_smoother        (rlai_control/control.launch.py)
  - EKF (robot_localization ekf_node)       (rlai_localization/localization.launch.py)
    The EKF provides /odometry/filtered and owns odom→base_footprint TF.

TF chain after this launch:
  map → odom          (slam_toolbox)
  odom → base_footprint  (EKF — already running)

Save the finished map:
  ros2 run nav2_map_server map_saver_cli -f ~/maps/warehouse

WARNING: Do NOT run simultaneously with AMCL (use_amcl:=true in simulation.launch.py).
Both publish map→odom.  Use mapping_enabled:=true OR use_amcl:=true, never both.

Usage:
  ros2 launch rlai_mapping mapping.launch.py
  ros2 launch rlai_mapping mapping.launch.py rviz_enabled:=false
  ros2 launch rlai_mapping mapping.launch.py slam_params_file:=/path/to/custom.yaml
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('rlai_mapping')

    default_slam_params = PathJoinSubstitution(
        [pkg, 'config', 'slam_toolbox_online_async.yaml']
    )
    slam_rviz = PathJoinSubstitution([pkg, 'rviz', 'mapping.rviz'])

    # ── Launch arguments ──────────────────────────────────────────────────
    declared_args = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock',
        ),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=default_slam_params,
            description='Full path to slam_toolbox YAML parameter file',
        ),
        DeclareLaunchArgument(
            'rviz_enabled',
            default_value='true',
            description='Launch RViz2 with SLAM overhead view',
        ),
    ]

    # ── async_slam_toolbox_node ───────────────────────────────────────────
    # Online async mode: builds map incrementally while robot navigates.
    # Publishes /map (nav_msgs/OccupancyGrid) and map→odom TF.
    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            LaunchConfiguration('slam_params_file'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    # ── map_saver_server ──────────────────────────────────────────────────
    # Provides /map_saver/save_map service.  Managed by lifecycle_manager
    # below.  Save a map with:
    #   ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map
    map_saver_server = Node(
        package='nav2_map_server',
        executable='map_saver_server',
        name='map_saver_server',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'save_map_timeout': 5.0,
            'free_thresh_default': 0.25,
            'occupied_thresh_default': 0.65,
        }],
    )

    # ── lifecycle_manager ─────────────────────────────────────────────────
    # Transitions slam_toolbox AND map_saver_server through
    # configure→activate automatically.
    # NOTE: slam_toolbox IS a lifecycle node in ROS 2 Jazzy and requires
    # external lifecycle management — it does NOT self-activate.
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_slam',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'autostart': True,
            'node_names': ['slam_toolbox', 'map_saver_server'],
        }],
    )

    # ── RViz2 (optional) ─────────────────────────────────────────────────
    # Overhead top-down view: Map, LaserScan, RobotModel, TF, EKF odometry.
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', slam_rviz],
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        condition=IfCondition(LaunchConfiguration('rviz_enabled')),
        output='screen',
    )

    return LaunchDescription(
        declared_args + [
            slam_node,
            map_saver_server,
            lifecycle_manager,
            rviz_node,
        ]
    )
