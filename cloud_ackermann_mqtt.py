#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math
import paho.mqtt.client as mqtt

class CloudAckermannMQTT(Node):
    def __init__(self):
        super().__init__('cloud_ackermann_mqtt')
        
        # 1. Настройка публичного MQTT-Брокера
        self.broker = "broker.hivemq.com"
        self.port = 1883
        # Уникальный топик, чтобы никто другой не перехватил команды
        self.topic = "openmower/cloud_hils_mk/command"
        
        self.mqtt_client = mqtt.Client()
        self.get_logger().info(f"Подключаюсь к публичному облаку {self.broker}...")
        
        try:
            self.mqtt_client.connect(self.broker, self.port, 60)
            self.mqtt_client.loop_start()
            self.get_logger().info("✅ Соединение с облачным брокером установлено!")
        except Exception as e:
            self.get_logger().error(f"❌ Ошибка MQTT: {e}")

        # Параметры трактора
        self.wheelbase_L = 0.50  
        
        # 2. Слушаем команды скорости от пульта (симулятора)
        self.subscription = self.create_subscription(Twist, '/cmd_vel_foxglove', self.cmd_vel_callback, 10)
        self.get_logger().info("Cloud Bridge Started: Сбор данных с /cmd_vel_foxglove")

    def cmd_vel_callback(self, msg):
        cmd_v = msg.linear.x
        cmd_w = msg.angular.z

        # Математика Аккермана (высчитываем угол руля)
        if abs(cmd_v) > 0.01:
            steering_rad = math.atan((cmd_w * self.wheelbase_L) / cmd_v)
        else:
            steering_rad = 0.0
            
        steering_rad = max(min(steering_rad, 0.785), -0.785)
        steering_deg = int(math.degrees(steering_rad))
        throttle = int(cmd_v * 100.0)

        # Строка для Ардуино
        command_str = f"S:{steering_deg}\nV:{throttle}\n"
        
        # 3. Транслируем команду в радиоэфир интернета!
        self.mqtt_client.publish(self.topic, command_str)
        # self.get_logger().info(f"Отправлено в облако: {command_str.strip()}")

def main(args=None):
    rclpy.init(args=args)
    node = CloudAckermannMQTT()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.mqtt_client.loop_stop()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
