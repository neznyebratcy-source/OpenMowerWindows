#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import tf2_ros

# Tree trunk obstacles from worlds/open_field.sdf: (x, y, radius_m)
OBSTACLES = [
    (-12.0,  11.0, 0.90),
    ( -7.0,  13.0, 1.08),
    ( -3.0,  13.0, 0.78),
    (  3.0,   8.0, 1.20),
    (  8.0,  13.0, 0.84),
    ( 13.0,   9.0, 0.96),
    (-13.0,   3.0, 1.02),
    ( -9.0,  -3.0, 0.78),
    ( -4.0,  -4.0, 0.90),
    ( 12.0,   4.0, 1.14),
    (  7.0,  -3.0, 0.72),
    (-12.0,  -8.0, 1.02),
    ( -8.0, -13.0, 0.96),
    (  2.0, -12.0, 1.20),
    ( 10.0,  -8.0, 0.84),
    ( 14.0, -13.0, 0.78),
    (  4.0,   3.0, 0.84),
    ( -3.0,  -8.0, 0.96),
]

NUM_RAYS  = 360
RANGE_MIN = 0.10
RANGE_MAX = 25.0


class SyntheticScan(Node):
    def __init__(self):
        super().__init__('synthetic_scan')
        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        self.tf  = tf2_ros.Buffer()
        tf2_ros.TransformListener(self.tf, self)
        self.create_timer(0.1, self._publish)

    def _publish(self):
        try:
            t = self.tf.lookup_transform('map', 'radar_link', rclpy.time.Time())
        except Exception:
            return

        rx  = t.transform.translation.x
        ry  = t.transform.translation.y
        q   = t.transform.rotation
        yaw = math.atan2(2.0*(q.w*q.z + q.x*q.y),
                         1.0 - 2.0*(q.y*q.y + q.z*q.z))

        angle_step = 2.0 * math.pi / NUM_RAYS
        ranges = [float('inf')] * NUM_RAYS

        for ox, oy, r in OBSTACLES:
            fx = rx - ox
            fy = ry - oy
            for i in range(NUM_RAYS):
                a  = yaw + (-math.pi + i * angle_step)
                dx = math.cos(a)
                dy = math.sin(a)
                b    = 2.0*(fx*dx + fy*dy)
                c    = fx*fx + fy*fy - r*r
                disc = b*b - 4.0*c
                if disc < 0.0:
                    continue
                sq  = math.sqrt(disc)
                t1  = (-b - sq) * 0.5
                t2  = (-b + sq) * 0.5
                hit = t1 if t1 >= RANGE_MIN else (t2 if t2 >= RANGE_MIN else None)
                if hit is not None and hit <= RANGE_MAX and hit < ranges[i]:
                    ranges[i] = hit

        msg = LaserScan()
        msg.header.stamp    = rclpy.time.Time().to_msg()
        msg.header.frame_id = 'radar_link'
        msg.angle_min       = -math.pi
        msg.angle_max       =  math.pi
        msg.angle_increment = angle_step
        msg.scan_time       = 0.1
        msg.range_min       = RANGE_MIN
        msg.range_max       = RANGE_MAX
        msg.ranges          = [float(v) for v in ranges]
        self.pub.publish(msg)


def main():
    rclpy.init()
    rclpy.spin(SyntheticScan())
    rclpy.shutdown()


if __name__ == '__main__':
    main()