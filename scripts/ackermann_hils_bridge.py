#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import math

class AckermannHILSBridge(Node):
    def __init__(self):
        super().__init__('ackermann_hils_bridge')
        
        # 1. Настройки Serial
        possible_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']
        self.baud_rate = 115200
        self.arduino = None
        
        for port in possible_ports:
            try:
                self.arduino = serial.Serial(port, self.baud_rate, timeout=0.1)
                self.get_logger().info(f"HIL Подключен: {port} 🎉")
                break
            except Exception:
                pass
                
        if not self.arduino:
            self.get_logger().error("HIL Без Arduino. Не найден ни один из портов (ttyUSB0, ttyACM0 и т.д.)! ❌")

        self.wheelbase_L = 0.50  
        
        # ROS 2 Sub - Слушаем команды скорости от пульта джойстика
        self.subscription = self.create_subscription(Twist, '/cmd_vel_foxglove', self.cmd_vel_callback, 10)
        self.get_logger().info("HILS Bridge Started: Eavesdropping on /cmd_vel_foxglove")

    def cmd_vel_callback(self, msg):
        cmd_v = msg.linear.x
        cmd_w = msg.angular.z

        # Математика Аккермана (высчитываем УГОЛ поворота переднего колеса в радианах)
        if abs(cmd_v) > 0.01:
            steering_rad = math.atan((cmd_w * self.wheelbase_L) / cmd_v)
        else:
            steering_rad = 0.0
            
        # Ограничиваем угол руля (макс 45 градусов = 0.785 рад)
        steering_rad = max(min(steering_rad, 0.785), -0.785)
        steering_deg = int(math.degrees(steering_rad))
        
        # Скорость маршевого двигателя (-100 до 100)
        throttle = int(cmd_v * 100.0)

        command_str = f"S:{steering_deg}\nV:{throttle}\n"
        
        if self.arduino and self.arduino.is_open:
            self.arduino.write(command_str.encode('utf-8'))

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
