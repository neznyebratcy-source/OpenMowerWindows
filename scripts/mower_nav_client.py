#!/usr/bin/env python3
"""
Obstacle-Aware Mowing Navigation Client
========================================
Generates a Boustrophedon (snake) coverage path inside a polygon,
publishes the intended path for Foxglove visualization, then sends
all waypoints to Nav2 via NavigateThroughPoses so the tractor
autonomously follows the pattern while dynamically avoiding obstacles.

Usage (inside the Docker container):
    python3 /opt/ws/mower_nav_client.py
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import NavigateThroughPoses
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from shapely.geometry import Polygon, LineString
import math
import time


# ───────────────────────────────────────────────────────────────
# DEMO POLYGON — fits inside the open_field.sdf tree layout
# Trees are scattered across a 30x30 m field centered at origin.
# This polygon carves out a ~12x10 m mowing zone in the center
# where several trees stand, forcing the planner to route around.
# Replace with real GPS-derived coordinates for field deployment.
# ───────────────────────────────────────────────────────────────
DEMO_POLYGON = [
    (-6.0, -6.0),
    ( 6.0, -6.0),
    ( 6.0,  6.0),
    (-6.0,  6.0),
]

MOWING_STRIP_WIDTH = 0.4   # meters between parallel passes
DRIVE_SPEED = 0.35         # m/s — conservative for demo


def generate_snake_path(polygon, spacing=0.4):
    """
    Generates a coverage path inside a Shapely polygon.
    1. Contour pass along the perimeter
    2. Boustrophedon (snake) fill of the interior
    """
    path_points = []

    # Contour pass — mow the edges first
    perimeter_coords = list(polygon.exterior.coords)
    path_points.extend(perimeter_coords)

    # Bounding box
    minx, miny, maxx, maxy = polygon.bounds
    left_to_right = True
    current_y = miny

    while current_y <= maxy:
        scan_line = LineString([(minx - 1, current_y), (maxx + 1, current_y)])
        intersection = scan_line.intersection(polygon)

        segments = []
        if intersection.is_empty:
            pass
        elif intersection.geom_type == 'LineString':
            segments.append(intersection)
        elif intersection.geom_type == 'MultiLineString':
            for geom in intersection.geoms:
                segments.append(geom)

        points = []
        for segment in segments:
            points.extend(list(segment.coords))

        if points:
            points = sorted(points, key=lambda p: p[0])
            if not left_to_right:
                points.reverse()
            path_points.extend(points)
            left_to_right = not left_to_right

        current_y += spacing

    return path_points


class MowerNavClient(Node):
    def __init__(self):
        super().__init__('mower_nav_client')

        # Action client for Nav2's NavigateThroughPoses
        self._action_client = ActionClient(
            self, NavigateThroughPoses, 'navigate_through_poses')

        # Publisher for Foxglove visualization of intended path
        self._path_pub = self.create_publisher(Path, '/intended_path', 10)

        self.get_logger().info('🚜 Mower Nav Client initialized')

    def make_pose(self, x, y, yaw=0.0):
        """Create a PoseStamped in the map frame."""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.position.z = 0.0
        # Convert yaw to quaternion (rotation around Z axis)
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    def publish_intended_path(self, waypoints):
        """Publish the snake path so Foxglove draws a glowing line."""
        path_msg = Path()
        path_msg.header.frame_id = 'map'
        path_msg.header.stamp = self.get_clock().now().to_msg()
        for (x, y) in waypoints:
            path_msg.poses.append(self.make_pose(x, y))
        self._path_pub.publish(path_msg)
        self.get_logger().info(
            f'📈 Published intended path with {len(waypoints)} waypoints to /intended_path')

    def send_goal(self, waypoints):
        """Send all waypoints to Nav2 as a single NavigateThroughPoses goal."""
        self.get_logger().info('⏳ Waiting for Nav2 action server...')
        self._action_client.wait_for_server()
        self.get_logger().info('✅ Nav2 action server is ready!')

        # Build the goal
        goal_msg = NavigateThroughPoses.Goal()
        for (x, y) in waypoints:
            goal_msg.poses.append(self.make_pose(x, y))

        self.get_logger().info(
            f'🚀 Sending {len(goal_msg.poses)} waypoints to Nav2...')
        self.get_logger().info(
            '   Nav2 will plan a global path that AVOIDS obstacles detected by radar.')

        send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self.feedback_callback)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('❌ Goal was REJECTED by Nav2!')
            return
        self.get_logger().info('✅ Goal ACCEPTED — tractor is moving!')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        # Log progress every few waypoints
        remaining = feedback_msg.feedback.number_of_poses_remaining
        if remaining % 5 == 0:
            self.get_logger().info(f'   📍 Waypoints remaining: {remaining}')

    def result_callback(self, future):
        result = future.result()
        self.get_logger().info('🏁 ========================================')
        self.get_logger().info('🏁  MOWING MISSION COMPLETE!')
        self.get_logger().info('🏁 ========================================')


def main(args=None):
    rclpy.init(args=args)
    node = MowerNavClient()

    # Generate the snake path
    polygon = Polygon(DEMO_POLYGON)
    node.get_logger().info(f'📐 Generating snake path inside polygon: {DEMO_POLYGON}')
    node.get_logger().info(f'   Strip width: {MOWING_STRIP_WIDTH}m')

    waypoints = generate_snake_path(polygon, spacing=MOWING_STRIP_WIDTH)
    node.get_logger().info(f'✅ Generated {len(waypoints)} waypoints')

    # Publish the full intended path for Foxglove visualization
    # (publish a few times to make sure Foxglove catches it)
    for _ in range(3):
        node.publish_intended_path(waypoints)
        time.sleep(0.5)

    # Send to Nav2
    node.send_goal(waypoints)

    # Spin until mission complete
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Mission cancelled by user')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
