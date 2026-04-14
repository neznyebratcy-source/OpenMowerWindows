#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import serial
import math
import time

class ArduinoBridge(Node):
    def __init__(self):
        super().__init__('arduino_bridge')
        
        # 1. Настройки Serial-порта (USB) к Arduino
        # На Linux (внутри шлюза Docker/Raspberry) это обычно /dev/ttyUSB0 или /dev/ttyACM0
        self.serial_port = '/dev/ttyUSB0'
        self.baud_rate = 115200
        
        try:
            self.arduino = serial.Serial(self.serial_port, self.baud_rate, timeout=0.1)
            self.get_logger().info(f"Успешно подключились к Arduino на {self.serial_port}")
        except Exception as e:
            self.get_logger().error(f"Не удалось открыть порт {self.serial_port}. Проверьте кабель! Ошибка: {e}")
            self.arduino = None

        # 2. Параметры вашего кастомного робота (ЗАМЕНИТЕ НА СВОИ!)
        self.wheel_base = 0.40  # Расстояние между левым и правым колесом (в метрах)
        self.wheel_radius = 0.15 # Радиус колеса (в метрах)
        
        # 3. Подписываемся на команды скорости от Навигатора (Nav2)
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10)
            
        # 4. Публикуем одометрию (куда мы приехали) обратно в Nav2
        self.odom_publisher = self.create_publisher(Odometry, '/odom', 10)
        
        # 5. Таймер для постоянного чтения ответов от Arduino (например, 20 раз в секунду)
        self.timer = self.create_timer(0.05, self.read_from_arduino)

    def cmd_vel_callback(self, msg):
        """
        Переводчик Направления в Обороты.
        Nav2 прислал команду: linear.x (едем вперед) и angular.z (поворот).
        """
        v = msg.linear.x    # Линейная скорость (м/с)
        w = msg.angular.z   # Угловая скорость (рад/с)

        # Прямая кинематика дифференциального привода
        # Высчитываем скорость для Левого (v_left) и Правого (v_right) колеса
        v_right = v + (w * self.wheel_base / 2.0)
        v_left = v - (w * self.wheel_base / 2.0)

        # Формируем СМСку для Arduino в формате "M:1.50,-1.50\n"
        command_str = f"M:{v_left:.2f},{v_right:.2f}\n"
        
        if self.arduino and self.arduino.is_open:
            self.arduino.write(command_str.encode('utf-8'))
            # Раскомментируйте строку ниже для дебага, чтобы видеть, что шлется в порт:
            # self.get_logger().info(f"В Arduino отправлено: {command_str.strip()}")

    def read_from_arduino(self):
        """
        Чтение ответа. Ардуино должна слать что-то вроде "E:1500,1505\n"
        где цифры - это количество тиков (щелчков) энкодеров.
        Пока оставляем заглушку, так как нужно знать, какие энкодеры вы купите.
        """
        if self.arduino and self.arduino.is_open:
            if self.arduino.in_waiting > 0:
                line = self.arduino.readline().decode('utf-8').strip()
                if line.startswith("E:"):
                    # Здесь будет математика перевода тиков энкодера в метры
                    # и публикация в self.odom_publisher!
                    pass

def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
