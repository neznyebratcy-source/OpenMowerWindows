#!/bin/bash
cd ~/OpenMowerWindows || exit

docker compose up -d

echo "Waiting for containers to start..."
sleep 15

echo "Starting twist relay..."
docker exec -it openmowerwindows-workspace-1 bash -c "cat > /tmp/relay.py << 'PYEOF'
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped

class RelayNode(Node):
    def __init__(self):
        super().__init__(\"twist_relay\")
        self.pub = self.create_publisher(TwistStamped, \"/diff_drive_base_controller/cmd_vel\", 10)
        self.sub = self.create_subscription(Twist, \"/cmd_vel_foxglove\", self.callback, 10)

    def callback(self, msg):
        out = TwistStamped()
        out.header.stamp = self.get_clock().now().to_msg()
        out.header.frame_id = \"base_link\"
        out.twist = msg
        self.pub.publish(out)

rclpy.init()
rclpy.spin(RelayNode())
PYEOF"

docker exec -d openmowerwindows-workspace-1 bash -c \
  "source /opt/ros/jazzy/setup.bash && \
   source /opt/ws/install/setup.bash && \
   python3 /tmp/relay.py"

echo ""
echo "✅ Simulation ready!"
echo "   Gazebo:   http://localhost:12345"
echo "   Foxglove: ws://localhost:8765"
