"""
rlai_gazebo/launch/gazebo.launch.py

Main Gazebo Harmonic simulation entrypoint.

What this launches:
  1. gz sim  — Gazebo server + GUI (world chosen via 'world' arg)
  2. robot_state_publisher  — publishes /robot_description and static TF
  3. ros_gz_sim/create  — spawns rlai_bot into the running world (TimerAction 3 s delay)
  4. ros_gz_bridge/parameter_bridge  — bridges topics per ros_gz_bridge.yaml

Usage:
  ros2 launch rlai_gazebo gazebo.launch.py
  ros2 launch rlai_gazebo gazebo.launch.py world:=empty x:=1.0 y:=2.0
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_gz = FindPackageShare("rlai_gazebo")
    pkg_desc = FindPackageShare("rlai_description")
    pkg_control = FindPackageShare("rlai_control")

    # Launch arguments
    declared_args = [
        DeclareLaunchArgument(
            "world",
            default_value="small_warehouse",
            description="World name (must match a .sdf file in rlai_gazebo/worlds/)",
        ),
        DeclareLaunchArgument("x",   default_value="0.0",
                              description="Robot spawn X position [m]"),
        DeclareLaunchArgument("y",   default_value="0.0",
                              description="Robot spawn Y position [m]"),
        DeclareLaunchArgument("z",   default_value="0.1",
                              description="Robot spawn Z position [m]"),
        DeclareLaunchArgument("yaw", default_value="0.0",
                              description="Robot spawn yaw angle [rad]"),
        DeclareLaunchArgument(
            "robot_namespace",
            default_value="",
            description="ROS namespace for all robot nodes (empty = no namespace)",
        ),
        # Sensor toggles must stay in sync with robot.urdf.xacro arguments.
        DeclareLaunchArgument("lidar_2d_enabled",     default_value="true"),
        DeclareLaunchArgument("lidar_3d_enabled",     default_value="false"),
        DeclareLaunchArgument("depth_camera_enabled", default_value="true"),
        DeclareLaunchArgument("stereo_camera_enabled", default_value="false"),
        DeclareLaunchArgument("imu_enabled",          default_value="true"),
        DeclareLaunchArgument("gps_enabled",          default_value="false"),
        DeclareLaunchArgument(
            "rviz_enabled",
            default_value="false",
            description="Launch RViz2 with the gazebo_live.rviz config",
        ),
        DeclareLaunchArgument(
            "headless",
            default_value="false",
            description="Run Gazebo server-only (no GUI). Physics and sensors remain active.",
        ),
    ]

    robot_description = ParameterValue(
        Command([
            FindExecutable(name="xacro"), " ",
            PathJoinSubstitution([pkg_desc, "urdf", "robot.urdf.xacro"]),
            " sim_mode:=gazebo",
            " robot_namespace:=",      LaunchConfiguration("robot_namespace"),
            " lidar_2d_enabled:=",     LaunchConfiguration("lidar_2d_enabled"),
            " lidar_3d_enabled:=",     LaunchConfiguration("lidar_3d_enabled"),
            " depth_camera_enabled:=", LaunchConfiguration("depth_camera_enabled"),
            " stereo_camera_enabled:=", LaunchConfiguration("stereo_camera_enabled"),
            " imu_enabled:=",          LaunchConfiguration("imu_enabled"),
            " gps_enabled:=",          LaunchConfiguration("gps_enabled"),
        ]),
        value_type=str,
    )

    gz_sim_gui = ExecuteProcess(
        cmd=[
            "gz", "sim", "-r",
            PathJoinSubstitution([pkg_gz, "worlds",
                                  [LaunchConfiguration("world"), ".sdf"]]),
        ],
        output="screen",
        condition=UnlessCondition(LaunchConfiguration("headless")),
    )
    gz_sim_headless = ExecuteProcess(
        cmd=[
            "gz", "sim", "-r", "-s",
            PathJoinSubstitution([pkg_gz, "worlds",
                                  [LaunchConfiguration("world"), ".sdf"]]),
        ],
        output="screen",
        condition=IfCondition(LaunchConfiguration("headless")),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[{
            "robot_description": robot_description,
            "use_sim_time": True,
        }],
    )

    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="ros_gz_sim",
                executable="create",
                name="spawn_rlai_bot",
                output="screen",
                arguments=[
                    "-topic", "robot_description",
                    "-name",  "rlai_bot",
                    "-x",  LaunchConfiguration("x"),
                    "-y",  LaunchConfiguration("y"),
                    "-z",  LaunchConfiguration("z"),
                    "-Y",  LaunchConfiguration("yaw"),
                ],
            )
        ],
    )

    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        output="screen",
        parameters=[{
            "config_file": PathJoinSubstitution(
                [pkg_gz, "config", "ros_gz_bridge.yaml"]
            ),
            "use_sim_time": True,
        }],
    )

    # Delay controller startup until Gazebo has loaded the ros2_control hardware interface.
    control_bringup = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [pkg_control, "launch", "control.launch.py"]
                    )
                ),
                launch_arguments={"use_sim_time": "true"}.items(),
            )
        ],
    )

    rviz2 = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        condition=IfCondition(LaunchConfiguration("rviz_enabled")),
        arguments=[
            "-d",
            PathJoinSubstitution([pkg_gz, "rviz", "gazebo_live.rviz"]),
        ],
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription(
        declared_args + [
            gz_sim_gui,
            gz_sim_headless,
            robot_state_publisher,
            spawn_robot,
            ros_gz_bridge,
            control_bringup,
            rviz2,
        ]
    )
