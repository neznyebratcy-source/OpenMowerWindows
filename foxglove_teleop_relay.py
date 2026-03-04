import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

class TeleopRelay(Node):
    def __init__(self):
        super().__init__('foxglove_teleop_relay')
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel_foxglove',
            self.listener_callback,
            10)
        self.publisher = self.create_publisher(TwistStamped, '/cmd_vel_joy', 10)
        self.get_logger().info('Foxglove Joystick Relay Started! Listening on /cmd_vel_foxglove -> /cmd_vel_joy')

    def listener_callback(self, msg):
        stamped_msg = TwistStamped()
        stamped_msg.header.stamp = self.get_clock().now().to_msg()
        stamped_msg.header.frame_id = 'base_link'
        stamped_msg.twist = msg
        self.publisher.publish(stamped_msg)

def main(args=None):
    rclpy.init(args=args)
    relay = TeleopRelay()
    rclpy.spin(relay)
    relay.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
