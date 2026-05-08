#!/usr/bin/env python3
"""
coverage_goal_bridge.py
=======================
Triggers coverage (snake) mowing via Nav2's NavigateToPose action.

Input:
  - /mowing_goal  (geometry_msgs/PoseStamped)  — publish a pose to start mowing

Works with any ROS 2 visualization tool (RViz, Foxglove, ros2 topic pub, etc.).
The robot navigates to the x/y position and the CoveragePlanner plugin generates
the boustrophedon path over the nearest operation area.

Final heading is ignored (yaw_goal_tolerance = 2π in nav2_params.yaml).
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose


class CoverageGoalBridge(Node):
    def __init__(self):
        super().__init__('coverage_goal_bridge')

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._active_goal   = None

        self.create_subscription(
            PoseStamped,
            '/mowing_goal',
            self._on_mowing_goal,
            10)

        self.get_logger().info(
            'coverage_goal_bridge ready — publish a PoseStamped to /mowing_goal to start mowing.')

    # ── /mowing_goal → NavigateToPose ─────────────────────────────────────────
    def _on_mowing_goal(self, pose: PoseStamped):
        self._send_goal(pose)

    # ── shared send logic ─────────────────────────────────────────────────────
    def _send_goal(self, pose: PoseStamped):
        self.get_logger().info(
            f'Goal received: x={pose.pose.position.x:.2f}  y={pose.pose.position.y:.2f}')

        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error(
                'NavigateToPose action server not available — is Nav2 running?')
            return

        if self._active_goal is not None:
            self.get_logger().info('Cancelling previous goal...')
            self._active_goal.cancel_goal_async()
            self._active_goal = None

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = pose
        goal_msg.behavior_tree = (
            '/opt/ws/install/open_mower_next/share/open_mower_next'
            '/config/coverage_bt.xml'
        )

        future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self._on_feedback)
        future.add_done_callback(self._on_goal_accepted)

    # ── action callbacks ──────────────────────────────────────────────────────
    def _on_goal_accepted(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Goal rejected by Nav2.')
            return
        self.get_logger().info('Goal accepted — navigating.')
        self._active_goal = goal_handle
        goal_handle.get_result_async().add_done_callback(self._on_result)

    def _on_feedback(self, feedback_msg):
        dist = feedback_msg.feedback.distance_remaining
        self.get_logger().info(
            f'  Distance remaining: {dist:.2f} m', throttle_duration_sec=3.0)

    def _on_result(self, future):
        result = future.result().result
        if result.error_code == 0:
            self.get_logger().info('Navigation completed successfully.')
        else:
            self.get_logger().warn(
                f'Navigation finished with error code {result.error_code}')
        self._active_goal = None


def main():
    rclpy.init()
    node = CoverageGoalBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()