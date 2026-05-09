"""Launch RViz with robot_state_publisher for offline URDF visualization."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
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
    pkg_share = FindPackageShare("rlai_description")

    sim_mode_arg = DeclareLaunchArgument(
        "sim_mode", default_value="gazebo",
        description="Hardware plugin selection: gazebo | isaac | real",
        choices=["gazebo", "isaac", "real"],
    )
    lidar_2d_arg = DeclareLaunchArgument(
        "lidar_2d_enabled", default_value="true",
        description="Include 2-D LiDAR link in the robot model",
    )
    lidar_3d_arg = DeclareLaunchArgument(
        "lidar_3d_enabled", default_value="false",
        description="Include 3-D LiDAR link in the robot model",
    )
    depth_camera_arg = DeclareLaunchArgument(
        "depth_camera_enabled", default_value="true",
        description="Include RGB-D depth camera links in the robot model",
    )
    stereo_camera_arg = DeclareLaunchArgument(
        "stereo_camera_enabled", default_value="false",
        description="Include stereo camera links in the robot model",
    )
    imu_arg = DeclareLaunchArgument(
        "imu_enabled", default_value="true",
        description="Include IMU link in the robot model",
    )
    gps_arg = DeclareLaunchArgument(
        "gps_enabled", default_value="false",
        description="Include GPS link in the robot model",
    )

    robot_description = ParameterValue(
        Command(
            [
                FindExecutable(name="xacro"), " ",
                PathJoinSubstitution([pkg_share, "urdf", "robot.urdf.xacro"]),
                " sim_mode:=",             LaunchConfiguration("sim_mode"),
                " lidar_2d_enabled:=",     LaunchConfiguration("lidar_2d_enabled"),
                " lidar_3d_enabled:=",     LaunchConfiguration("lidar_3d_enabled"),
                " depth_camera_enabled:=", LaunchConfiguration("depth_camera_enabled"),
                " stereo_camera_enabled:=", LaunchConfiguration("stereo_camera_enabled"),
                " imu_enabled:=",          LaunchConfiguration("imu_enabled"),
                " gps_enabled:=",          LaunchConfiguration("gps_enabled"),
            ]
        ),
        value_type=str,
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[{
            "robot_description": robot_description,
            "use_sim_time": False,
        }],
    )

    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
    )

    rviz2 = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=[
            "-d", PathJoinSubstitution([pkg_share, "rviz", "robot_model.rviz"])
        ],
    )

    return LaunchDescription(
        [
            sim_mode_arg,
            lidar_2d_arg,
            lidar_3d_arg,
            depth_camera_arg,
            stereo_camera_arg,
            imu_arg,
            gps_arg,
            robot_state_publisher,
            joint_state_publisher_gui,
            rviz2,
        ]
    )
