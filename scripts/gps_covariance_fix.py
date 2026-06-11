#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix

class GPSCovarianceFix(Node):
    def __init__(self):
        super().__init__('gps_covariance_fix')
        
        # Подписываемся на сырые данные из Gazebo
        self.sub = self.create_subscription(
            NavSatFix,
            '/gps/fix',
            self.gps_callback,
            10
        )
        
        # Публикуем исправленные данные
        self.pub = self.create_publisher(NavSatFix, '/gps/fix_fixed', 10)
        self.get_logger().info('GPS Covariance Fix Node started. Injecting variance.')

    def gps_callback(self, msg):
        # Создаем копию сообщения
        fixed_msg = NavSatFix()
        fixed_msg.header = msg.header
        fixed_msg.status = msg.status
        fixed_msg.latitude = msg.latitude
        fixed_msg.longitude = msg.longitude
        fixed_msg.altitude = msg.altitude
        
        # Устанавливаем тип ковариации: COVARIANCE_TYPE_APPROXIMATED (1)
        fixed_msg.position_covariance_type = 1
        
                # Удаляем перевод в градусы!
        # variance_xy = 3.63e-10
        # variance_z = 1.44e-9 

        # Устанавливаем дисперсию в КВАДРАТНЫХ МЕТРАХ.
        # stddev = 2.12 метра. Дисперсия = 2.12^2 = 4.49 м^2.
        variance_xy = 300.0
        
        # Для высоты делаем дисперсию еще больше, 
        # чтобы EKF меньше доверял диким прыжкам высоты из Gazebo.
        # Допустим, stddev = 10 метров. Дисперсия = 100 м^2.
        variance_z = 1000000.0

        # Матрица: [XX, XY, XZ, YX, YY, YZ, ZX, ZY, ZZ]
        fixed_msg.position_covariance = [
            variance_xy, 0.0, 0.0,
            0.0, variance_xy, 0.0,
            0.0, 0.0, variance_z
        ]
        
        self.pub.publish(fixed_msg)

def main(args=None):
    rclpy.init(args=args)
    node = GPSCovarianceFix()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
