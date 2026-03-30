#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
import serial
import math
import time
from tf2_ros import TransformBroadcaster
from transforms3d.euler import euler2quat

class AckermannHILSBridge(Node):
    def __init__(self):
        super().__init__('ackermann_hils_bridge')
        
        # 1. Настройки Serial
        self.serial_port = '/dev/ttyUSB0'
        self.baud_rate = 115200
        try:
            self.arduino = serial.Serial(self.serial_port, self.baud_rate, timeout=0.1)
            self.get_logger().info(f"HIL Подключен: {self.serial_port}")
        except Exception as e:
            self.get_logger().error(f"HIL Без Arduino (чистая симуляция). Ошибка: {e}")
            self.arduino = None

        # 2. Параметры Аккермана вашего трактора
        # L - Расстояние от задней (ведущей) оси до передней (рулевой) оси
        self.wheelbase_L = 0.50  

        # 3. Переменные фейковой симуляции одометрии (мы спавнимся в координате 0,0)
        self.fake_x = 0.0
        self.fake_y = 0.0
        self.fake_theta = 0.0
        self.last_time = time.time()
        
        # Последние команды от Навигатора
        self.cmd_v = 0.0
        self.cmd_w = 0.0

        # ROS 2 Pub/Sub
        self.subscription = self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.odom_publisher = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Цикл симулятора (работает 20 раз в секунду)
        self.timer = self.create_timer(0.05, self.hils_loop)

    def cmd_vel_callback(self, msg):
        """Когда приходит команда от Nav2, сохраняем её для симулятора и шлем в Arduino"""
        self.cmd_v = msg.linear.x
        self.cmd_w = msg.angular.z

        # Математика Аккермана (высчитываем УГОЛ поворота переднего колеса в радианах)
        # delta = arctan( w * L / v )
        if abs(self.cmd_v) > 0.01:
            steering_rad = math.atan((self.cmd_w * self.wheelbase_L) / self.cmd_v)
        else:
            steering_rad = 0.0
            
        # Ограничиваем угол руля (макс 45 градусов = 0.785 рад)
        steering_rad = max(min(steering_rad, 0.785), -0.785)
        steering_deg = int(math.degrees(steering_rad))
        
        # Скорость маршевого двигателя (-100 до 100)
        throttle = int(self.cmd_v * 100.0)

        command_str = f"S:{steering_deg}\nV:{throttle}\n"
        
        if self.arduino and self.arduino.is_open:
            self.arduino.write(command_str.encode('utf-8'))

    def hils_loop(self):
        """Интегрируем полученные команды и врем Навигатору, что мы реально едем"""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Симулируем движение с помощью простой Эйлеровой интеграции идеальной модели движения
        self.fake_x += self.cmd_v * math.cos(self.fake_theta) * dt
        self.fake_y += self.cmd_v * math.sin(self.fake_theta) * dt
        self.fake_theta += self.cmd_w * dt

        timestamp = self.get_clock().now().to_msg()

        # Публикуем Фейковый Transform (tf2) map -> odom
        t = TransformStamped()
        t.header.stamp = timestamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.fake_x
        t.transform.translation.y = self.fake_y
        t.transform.translation.z = 0.0
        
        q = euler2quat(0, 0, self.fake_theta)  # roll, pitch, yaw
        t.transform.rotation.w = q[0]
        t.transform.rotation.x = q[1]
        t.transform.rotation.y = q[2]
        t.transform.rotation.z = q[3]
        
        self.tf_broadcaster.sendTransform(t)

        # Публикуем ஃபейковую Одометрию (Ответ на /cmd_vel)
        odom = Odometry()
        odom.header.stamp = timestamp
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = self.fake_x
        odom.pose.pose.position.y = self.fake_y
        
        odom.pose.pose.orientation.w = q[0]
        odom.pose.pose.orientation.x = q[1]
        odom.pose.pose.orientation.y = q[2]
        odom.pose.pose.orientation.z = q[3]
        
        odom.twist.twist.linear.x = self.cmd_v
        odom.twist.twist.angular.z = self.cmd_w
        
        self.odom_publisher.publish(odom)

def main(args=None):
    rclpy.init(args=args)
    node = AckermannHILSBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
