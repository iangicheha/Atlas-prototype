"""nav_client.py — Programmatic NavigateToPose action client for rlai_navigation.

Usage examples
--------------
# Send a single goal:
ros2 run rlai_navigation nav_client

# Override goal coordinates via CLI args:
ros2 run rlai_navigation nav_client --ros-args -p x:=3.0 -p y:=2.0 -p yaw:=0.0

# Send a patrol (series of waypoints) using the FollowWaypoints action:
ros2 run rlai_navigation nav_client --ros-args -p mode:=patrol

The client prints feedback (distance remaining, estimated time remaining) and
the final result (succeeded / failed / cancelled) to stdout.
"""

import math
import sys

from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import FollowWaypoints, NavigateToPose
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node


def yaw_to_quaternion(yaw: float) -> Quaternion:
    """Convert a yaw angle (radians) to a geometry_msgs/Quaternion."""
    q = Quaternion()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


def make_pose(x: float, y: float, yaw: float, frame_id: str = 'map') -> PoseStamped:
    """Build a PoseStamped message for the given 2-D pose."""
    ps = PoseStamped()
    ps.header.frame_id = frame_id
    ps.pose.position.x = x
    ps.pose.position.y = y
    ps.pose.position.z = 0.0
    ps.pose.orientation = yaw_to_quaternion(yaw)
    return ps


class NavClient(Node):
    """ROS 2 node that wraps the NavigateToPose and FollowWaypoints action clients."""

    # Waypoints used in patrol mode (small_warehouse.sdf frame, in metres).
    PATROL_WAYPOINTS = [
        (2.0,  1.5, 0.0),    # aisle end A
        (2.0, -1.5, 0.0),    # aisle end B
        (-2.0, -1.5, math.pi),  # aisle end C
        (-2.0,  1.5, math.pi),  # aisle end D
    ]

    def __init__(self):
        super().__init__('nav_client')

        # Declare parameters with sensible defaults.
        self.declare_parameter('x',    3.0)
        self.declare_parameter('y',    2.0)
        self.declare_parameter('yaw',  0.0)
        self.declare_parameter('mode', 'single')  # 'single' | 'patrol'

        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._wp_client = ActionClient(self, FollowWaypoints, 'follow_waypoints')

        self._result_received = False
        self._success = False

    def navigate_to(self, x: float, y: float, yaw: float) -> bool:
        """Send a single NavigateToPose goal and block until it finishes.

        Returns True if the robot reached the goal, False otherwise.
        """
        self.get_logger().info('Waiting for navigate_to_pose action server …')
        if not self._nav_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('navigate_to_pose action server not available.')
            return False

        goal = NavigateToPose.Goal()
        goal.pose = make_pose(x, y, yaw)
        # Set goal.behavior_tree to override the default BT for this request.

        self.get_logger().info(f'Sending goal  x={x:.2f}  y={y:.2f}  yaw={yaw:.2f} rad')
        send_future = self._nav_client.send_goal_async(
            goal,
            feedback_callback=self._feedback_cb,
        )
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            self.get_logger().error('Goal was rejected by the action server.')
            return False

        self.get_logger().info('Goal accepted — navigating …')
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result()
        # NavigateToPose does not expose a boolean; check the status code.
        # GoalStatus: SUCCEEDED = 4
        from action_msgs.msg import GoalStatus
        success = (result.status == GoalStatus.STATUS_SUCCEEDED)
        if success:
            self.get_logger().info('Goal reached successfully.')
        else:
            self.get_logger().warning(f'Navigation failed (status={result.status}).')
        return success

    def patrol(self) -> None:
        """Send all PATROL_WAYPOINTS to the FollowWaypoints action server.

        Blocks until the patrol finishes or fails.
        """
        self.get_logger().info('Waiting for follow_waypoints action server …')
        if not self._wp_client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error('follow_waypoints action server not available.')
            return

        goal = FollowWaypoints.Goal()
        goal.poses = [make_pose(x, y, yaw) for x, y, yaw in self.PATROL_WAYPOINTS]

        self.get_logger().info(
            f'Starting patrol with {len(goal.poses)} waypoints …')
        send_future = self._wp_client.send_goal_async(
            goal,
            feedback_callback=self._waypoint_feedback_cb,
        )
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()

        if not goal_handle.accepted:
            self.get_logger().error('Patrol goal was rejected.')
            return

        self.get_logger().info('Patrol goal accepted.')
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result()
        missed = result.result.missed_waypoints
        if missed:
            self.get_logger().warning(
                f'Patrol completed with {len(missed)} missed waypoint(s): {list(missed)}')
        else:
            self.get_logger().info('Patrol completed — all waypoints reached.')

    def _feedback_cb(self, feedback_msg) -> None:
        fb = feedback_msg.feedback
        self.get_logger().info(
            f'  distance remaining: {fb.distance_remaining:.2f} m  |  '
            f'ETA: {fb.estimated_time_remaining.sec} s',
            throttle_duration_sec=1.0,
        )

    def _waypoint_feedback_cb(self, feedback_msg) -> None:
        fb = feedback_msg.feedback
        self.get_logger().info(
            f'  current waypoint index: {fb.current_waypoint}',
            throttle_duration_sec=2.0,
        )


def main(args=None) -> None:
    rclpy.init(args=args)
    node = NavClient()

    mode = node.get_parameter('mode').get_parameter_value().string_value

    if mode == 'patrol':
        node.patrol()
    else:
        x = node.get_parameter('x').get_parameter_value().double_value
        y = node.get_parameter('y').get_parameter_value().double_value
        yaw = node.get_parameter('yaw').get_parameter_value().double_value
        success = node.navigate_to(x, y, yaw)
        sys.exit(0 if success else 1)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
