"""
rlai_teleop/estop_node.py

Emergency-stop node for rbot.

This is a software stop only; it does not replace a hardware emergency-stop circuit.

Provides the /e_stop service (std_srvs/srv/Trigger).  Each call toggles the
e-stop state:
  - ENGAGED  → publishes zero-velocity TwistStamped to /cmd_vel at 10 Hz until released
  - RELEASED → stops publishing; normal teleop/nav2 commands resume

The zero-velocity stream overrides incoming commands because the EStop node's
publisher shares /cmd_vel with teleop and nav2.  Downstream consumers (the
velocity_smoother) will see the zero command and halt the robot.

Usage:
  ros2 service call /e_stop std_srvs/srv/Trigger {}
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from std_srvs.srv import Trigger


class EStopNode(Node):
    def __init__(self) -> None:
        super().__init__('estop_node')

        self._stopped: bool = False

        self._pub = self.create_publisher(TwistStamped, 'cmd_vel', 1)
        self._srv = self.create_service(Trigger, 'e_stop', self._handle_estop)

        # Re-publish zero velocity while e-stop is active.
        self._timer = self.create_timer(0.1, self._timer_cb)  # 10 Hz

        self.get_logger().info(
            'EStop node ready — call /e_stop (std_srvs/Trigger) to engage/release'
        )

    def _handle_estop(
        self,
        request: Trigger.Request,
        response: Trigger.Response,
    ) -> Trigger.Response:
        self._stopped = not self._stopped

        if self._stopped:
            self._publish_zero()
            response.success = True
            response.message = 'E-stop ENGAGED — robot halted'
            self.get_logger().warn('E-stop ENGAGED')
        else:
            response.success = True
            response.message = 'E-stop RELEASED — teleoperation resumed'
            self.get_logger().info('E-stop RELEASED')

        return response

    def _timer_cb(self) -> None:
        if self._stopped:
            self._publish_zero()

    def _publish_zero(self) -> None:
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_footprint'
        self._pub.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = EStopNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
