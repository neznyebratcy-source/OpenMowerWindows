#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy

RESOLUTION = 0.05
ORIGIN_X   = -30.0
ORIGIN_Y   = -30.0
WIDTH_M    =  60.0
HEIGHT_M   =  60.0

OBSTACLES = [
    (-12.0, 11.0, 0.90), ( -7.0, 13.0, 1.08), ( -3.0, 13.0, 0.78),
    (  3.0,  8.0, 1.20), (  8.0, 13.0, 0.84), ( 13.0,  9.0, 0.96),
    (-13.0,  3.0, 1.02), ( -9.0, -3.0, 0.78), ( -4.0, -4.0, 0.90),
    ( 12.0,  4.0, 1.14), (  7.0, -3.0, 0.72), (-12.0, -8.0, 1.02),
    ( -8.0,-13.0, 0.96), (  2.0,-12.0, 1.20), ( 10.0, -8.0, 0.84),
    ( 14.0,-13.0, 0.78), (  4.0,  3.0, 0.84), ( -3.0, -8.0, 0.96),
]


class ObstacleMapPublisher(Node):
    def __init__(self):
        super().__init__('obstacle_map_publisher')
        qos = QoSProfile(
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.pub  = self.create_publisher(OccupancyGrid, '/obstacle_map', qos)
        self._msg = self._build_map()
        self.create_timer(2.0, self._publish)
        self._publish()

    def _build_map(self):
        W = int(WIDTH_M  / RESOLUTION)
        H = int(HEIGHT_M / RESOLUTION)
        data = [0] * (W * H)

        for ox, oy, radius in OBSTACLES:
            cx = int((ox - ORIGIN_X) / RESOLUTION)
            cy = int((oy - ORIGIN_Y) / RESOLUTION)
            r  = int(math.ceil(radius / RESOLUTION))
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx*dx + dy*dy <= r*r:
                        px, py = cx + dx, cy + dy
                        if 0 <= px < W and 0 <= py < H:
                            data[py * W + px] = 100

        msg = OccupancyGrid()
        msg.header.frame_id         = 'map'
        msg.info.resolution         = RESOLUTION
        msg.info.width              = W
        msg.info.height             = H
        msg.info.origin.position.x  = ORIGIN_X
        msg.info.origin.position.y  = ORIGIN_Y
        msg.data                    = data
        return msg

    def _publish(self):
        self._msg.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(self._msg)


def main():
    rclpy.init()
    rclpy.spin(ObstacleMapPublisher())
    rclpy.shutdown()


if __name__ == '__main__':
    main()