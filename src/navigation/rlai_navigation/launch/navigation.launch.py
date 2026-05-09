"""Launch the Nav2 planning, control, recovery, and behavior-tree stack.

The localization stack owns map_server, AMCL, and map->odom.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    pkg = FindPackageShare('rlai_navigation')
    nav2_params_yaml = PathJoinSubstitution([pkg, 'config', 'nav2_params.yaml'])

    declared_args = [
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock',
        ),
    ]

    # Navigation planning and control nodes

    # SMAC Hybrid-A* global planner.
    # Owns the global_costmap; publishes /plan on goal dispatch.
    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        name='planner_server',
        output='screen',
        parameters=[
            nav2_params_yaml,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    # SimpleSmoother applied to the global path before the controller receives it.
    smoother_server = Node(
        package='nav2_smoother',
        executable='smoother_server',
        name='smoother_server',
        output='screen',
        parameters=[
            nav2_params_yaml,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    # MPPI local controller.
    # Owns the local_costmap; publishes /cmd_vel, /local_plan, /trajectories.
    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        name='controller_server',
        output='screen',
        parameters=[
            nav2_params_yaml,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    # Multi-goal waypoint sequencer — FollowWaypoints action server.
    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        name='waypoint_follower',
        output='screen',
        parameters=[
            nav2_params_yaml,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    # Transitions all navigation nodes through configure→activate.
    lifecycle_manager_navigation = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[
            nav2_params_yaml,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    # Recovery behavior and behavior-tree nodes

    # Recovery behavior plugins: spin, backup, drive_on_heading, wait.
    # bt_navigator calls these action servers when a navigation step fails.
    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        name='behavior_server',
        output='screen',
        parameters=[
            nav2_params_yaml,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    # Behavior tree orchestrator.
    # Exposes NavigateToPose + FollowWaypoints action servers.
    # Resolves BT XML files from the rlai_navigation package share directory.
    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        name='bt_navigator',
        output='screen',
        parameters=[
            nav2_params_yaml,
            {
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                # Resolve the default BT XML to the full installed share path.
                # In Nav2 Jazzy the param was renamed from default_bt_xml_filename.
                'default_nav_to_pose_bt_xml': PathJoinSubstitution([
                    pkg, 'behavior_trees', 'navigate_to_pose.xml'
                ]),
            },
        ],
    )

    # Transitions behavior_server → bt_navigator to ACTIVE.
    # Started last so action servers are already ACTIVE
    # before bt_navigator attempts to connect to them.
    lifecycle_manager_behavior = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_behavior',
        output='screen',
        parameters=[
            nav2_params_yaml,
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    return LaunchDescription(
        declared_args + [
            planner_server,
            smoother_server,
            controller_server,
            waypoint_follower,
            lifecycle_manager_navigation,
            behavior_server,
            bt_navigator,
            lifecycle_manager_behavior,
        ]
    )
