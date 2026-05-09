"""
rlai_bringup/launch/simulation.launch.py

Top-level simulation entrypoint — delegates to the simulator-specific launch file.

Supported backend:
  gazebo  — rlai_gazebo/launch/gazebo.launch.py

All sensor-toggle and pose arguments are forwarded to the delegate launch file.

Usage:
  ros2 launch rlai_bringup simulation.launch.py
  ros2 launch rlai_bringup simulation.launch.py simulator:=gazebo world:=empty
  ros2 launch rlai_bringup simulation.launch.py mapping_enabled:=true
  ros2 launch rlai_bringup simulation.launch.py use_amcl:=true map_yaml_file:=/path/to/map.yaml

WARNING: mapping_enabled and use_amcl are mutually exclusive — both publish
         map->odom.  Use one or the other, never both simultaneously.
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    EqualsSubstitution,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.substitutions import FindPackageShare


def _as_bool(context, name):
    return LaunchConfiguration(name).perform(context).lower() in ("1", "true", "yes", "on")


def _validate_global_localization(context):
    if _as_bool(context, "mapping_enabled") and _as_bool(context, "use_amcl"):
        raise RuntimeError(
            "mapping_enabled and use_amcl cannot both be true because both publish map->odom"
        )
    return []


def generate_launch_description():

    # Launch arguments
    declared_args = [
        DeclareLaunchArgument(
            "simulator",
            default_value="gazebo",
            description="Simulator backend: 'gazebo' or 'isaac'",
            choices=["gazebo", "isaac"],
        ),
        DeclareLaunchArgument("world",                default_value="small_warehouse"),
        DeclareLaunchArgument("x",                    default_value="1.0"),
        DeclareLaunchArgument("y",                    default_value="1.0"),
        DeclareLaunchArgument("z",                    default_value="0.1"),
        DeclareLaunchArgument("yaw",                  default_value="0.0"),
        DeclareLaunchArgument(
            "headless",
            default_value="false",
            description="Run Gazebo server-only (no GUI). Physics and sensors remain active.",
        ),
        DeclareLaunchArgument("robot_namespace",      default_value=""),
        DeclareLaunchArgument("lidar_2d_enabled",     default_value="true"),
        DeclareLaunchArgument("lidar_3d_enabled",     default_value="false"),
        DeclareLaunchArgument("depth_camera_enabled", default_value="true"),
        DeclareLaunchArgument("stereo_camera_enabled", default_value="false"),
        DeclareLaunchArgument("imu_enabled",          default_value="true"),
        DeclareLaunchArgument("gps_enabled",          default_value="false"),
        DeclareLaunchArgument(
            "teleop_enabled",
            default_value="false",
            description="Launch joystick teleoperation stack (requires a joystick device)",
        ),
        DeclareLaunchArgument(
            "localization_enabled",
            default_value="true",
            description="Launch EKF localization stack (robot_localization ekf_node)",
        ),
        DeclareLaunchArgument(
            "use_amcl",
            default_value="false",
            description="Start AMCL + map_server for global localisation (requires map_yaml_file)",
        ),
        DeclareLaunchArgument(
            "map_yaml_file",
            default_value="",
            description="Absolute path to map YAML file (required when use_amcl:=true)",
        ),
        DeclareLaunchArgument(
            "camera_processing_enabled",
            default_value="true",
            description="Launch stereo rectification, disparity, and depth point-cloud processing.",
        ),
        DeclareLaunchArgument(
            "mapping_enabled",
            default_value="false",
            description=(
                "Launch slam_toolbox online-async mapping stack. "
                "Mutually exclusive with use_amcl:=true — both publish map->odom."
            ),
        ),
        DeclareLaunchArgument(
            "slam_rviz_enabled",
            default_value="false",
            description=(
                "Launch RViz2 with SLAM overhead view "
                "(only used when mapping_enabled:=true)"
            ),
        ),
    ]

    forward_args = {
        "world":                 LaunchConfiguration("world"),
        "x":                     LaunchConfiguration("x"),
        "y":                     LaunchConfiguration("y"),
        "z":                     LaunchConfiguration("z"),
        "yaw":                   LaunchConfiguration("yaw"),
        "robot_namespace":       LaunchConfiguration("robot_namespace"),
        "lidar_2d_enabled":      LaunchConfiguration("lidar_2d_enabled"),
        "lidar_3d_enabled":      LaunchConfiguration("lidar_3d_enabled"),
        "depth_camera_enabled":  LaunchConfiguration("depth_camera_enabled"),
        "stereo_camera_enabled": LaunchConfiguration("stereo_camera_enabled"),
        "imu_enabled":           LaunchConfiguration("imu_enabled"),
        "gps_enabled":           LaunchConfiguration("gps_enabled"),
        "headless":              LaunchConfiguration("headless"),
    }

    gazebo_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("rlai_gazebo"), "launch", "gazebo.launch.py"]
            )
        ),
        launch_arguments=forward_args.items(),
        condition=IfCondition(
            EqualsSubstitution(LaunchConfiguration("simulator"), "gazebo")
        ),
    )

    # Teleop is opt-in so navigation-only sessions are not cluttered with unused nodes.
    teleop_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("rlai_teleop"), "launch", "teleop.launch.py"]
            )
        ),
        launch_arguments={"use_sim_time": "true"}.items(),
        condition=IfCondition(LaunchConfiguration("teleop_enabled")),
    )

    # EKF provides odom->base_footprint; AMCL adds map->odom when use_amcl is true.
    localization_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("rlai_localization"), "launch", "localization.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time": "true",
            "use_amcl": LaunchConfiguration("use_amcl"),
            "map_yaml_file": LaunchConfiguration("map_yaml_file"),
        }.items(),
        condition=IfCondition(LaunchConfiguration("localization_enabled")),
    )

    camera_processing_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("rlai_camera_processing"),
                    "launch",
                    "camera_processing.launch.py",
                ]
            )
        ),
        launch_arguments={
            "use_sim_time": "true",
            "depth_camera_enabled": LaunchConfiguration("depth_camera_enabled"),
            "stereo_camera_enabled": LaunchConfiguration("stereo_camera_enabled"),
        }.items(),
        condition=IfCondition(LaunchConfiguration("camera_processing_enabled")),
    )

    # Do not enable mapping and AMCL together; both publish map->odom.
    mapping_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("rlai_mapping"), "launch", "mapping.launch.py"]
            )
        ),
        launch_arguments={
            "use_sim_time":  "true",
            "rviz_enabled":  LaunchConfiguration("slam_rviz_enabled"),
        }.items(),
        condition=IfCondition(LaunchConfiguration("mapping_enabled")),
    )

    # Isaac backend is reserved for future integration.

    return LaunchDescription(
        declared_args + [
            OpaqueFunction(function=_validate_global_localization),
            gazebo_bringup,
            teleop_bringup,
            localization_bringup,
            camera_processing_bringup,
            mapping_bringup,
        ]
    )
