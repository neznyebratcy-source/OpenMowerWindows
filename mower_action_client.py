#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import NavigateToPose
import math
import time

# Импортируем нашу математику змейки!
from test_snake_path import generate_snake_path
from shapely.geometry import Polygon

def get_quaternion_from_euler(roll, pitch, yaw):
    """Шпаргалка для перевода плоского угла в 3D кватернион (Nav2 требует именно его)"""
    qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    return Quaternion(x=qx, y=qy, z=qz, w=qw)

class MowerActionClient(Node):
    def __init__(self):
        super().__init__('mower_action_client')
        
        # Подключаемся к мозгу автопилота Nav2
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self.get_logger().info("🚜 Жду включения сервера /navigate_to_pose (Nav2)...")
        self._action_client.wait_for_server()
        self.get_logger().info("✅ Подключено к Nav2! Генерируем карту кошения...")

        # Наш самый сложный многоугольник
        lawn_coords = [
            (0.0, 0.0),      
            (8.5, -2.1),     
            (13.2, 4.8),     
            (9.0, 8.5),      
            (11.5, 14.2),    
            (4.0, 16.0),     
            (-2.5, 12.0),    
            (0.0, 7.5),      
            (-5.5, 4.0)      
        ]
        polygon = Polygon(lawn_coords)
        
        # ВЫЗЫВАЕМ НАШУ МАТЕМАТИКУ ИЗ СОСЕДНЕГО ФАЙЛА (Шаг 0.4м)
        self.path_points = generate_snake_path(polygon, spacing=0.4)
        self.current_point_index = 0
        
        self.get_logger().info(f"🗺️ Сгенерировано {len(self.path_points)} точек для кошения!")
        
        # Даем Nav2 секунду на "осознание себя" и погнали!
        time.sleep(1.0)
        self.send_next_goal()

    def send_next_goal(self):
        if self.current_point_index >= len(self.path_points):
            self.get_logger().info("🎉 ЗМЕЙКА ЗАВЕРШЕНА! Газон идеально покошен.")
            return

        p1 = self.path_points[self.current_point_index]
        
        # Вычисляем, куда трактор должен смотреть "лицом"
        yaw = 0.0
        if self.current_point_index + 1 < len(self.path_points):
            p2 = self.path_points[self.current_point_index + 1]
            yaw = math.atan2(p2[1] - p1[1], p2[0] - p1[0])

        goal_msg = NavigateToPose.Goal()
        # Важно! Координаты относительно карты, а не самого трактора
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        
        goal_msg.pose.pose.position.x = float(p1[0])
        goal_msg.pose.pose.position.y = float(p1[1])
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation = get_quaternion_from_euler(0, 0, yaw)

        self.get_logger().info(f"🚀 Едем к точке {self.current_point_index + 1}/{len(self.path_points)}: [X:{p1[0]:.2f}, Y:{p1[1]:.2f}]")

        # Отправляем "заказ на такси" в Nav2
        self.send_goal_future = self._action_client.send_goal_async(goal_msg)
        self.send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("❌ Nav2 отказался ехать туда!")
            return

        self.get_logger().info("⏳ Автопилот строит маршрут и едет...")
        self.get_result_future = goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        status = future.result().status
        # 4 - Это статус SUCCEEDED в ROS 2 Action
        if status == 4:
            self.get_logger().info("🎯 Точка достигнута!")
            self.current_point_index += 1
            # Небольшая пауза, чтобы трактор не дергался как сумасшедший
            time.sleep(0.5)
            self.send_next_goal()
        else:
            self.get_logger().error(f"⚠️ Трактор застрял или сорвался! Статус: {status}")
            # Пытаемся поехать к следующей точке, если эту провалили
            self.current_point_index += 1
            self.send_next_goal()

def main(args=None):
    rclpy.init(args=args)
    node = MowerActionClient()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
