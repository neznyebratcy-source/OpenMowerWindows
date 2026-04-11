# Implementation Guide: Foxglove Simulation Demo (Part 1)

This guide outlines the exact technical steps to transform Foxglove into a cinematic, investor-ready simulation dashboard (with virtual trees and path lines) for next week's pitch.

---

## Step 1: Configuring the Foxglove Layout (The Clean Dashboard)
No complex coding is required for the UI. We will configure it manually and export the configuration to lock it down.

1. Start your local simulation (`docker compose up`) and open **Foxglove Studio** on the presentation tablet or laptop.
2. Connect to the tractor's data stream via the `WebSocket` connection (URL: `ws://localhost:8765`).
3. Clear the default, messy engineering layout.
4. Add a single, massive **3D Panel** covering 90% of the screen. 
   - In the settings of the 3D Panel, toggle on `TF` (Transformations) to render the 3D physical model of the tractor, and toggle on the `/map` topic to see the ground grid.
5. Add a small **Teleop** or **Raw Messages** panel in the corner purely to allow you to trigger the Python autopilot script with the tap of a button.
6. Go to the top menu (or press `Ctrl+E`) and click **Export Layout**. Save this file as `investor_demo.json`. On the day of the pitch, you simply import this file, and the tablet is instantly ready.

---

## Step 2: Injecting "Virtual Trees" (The 3D Holograms)
To make the map look like a real park or complex environment, we will publish fake 3D objects to Foxglove. We use the fundamental `visualization_msgs/MarkerArray` message for this.

**1. Create the Spawner Script (`spawn_virtual_trees.py`)**
Create this Python script in your workspace. It will beam 3D coordinates to Foxglove.

```python
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray

class VirtualLandscape(Node):
    def __init__(self):
        super().__init__('virtual_landscape_spawner')
        # We publish to a custom topic that Foxglove will listen to
        self.publisher = self.create_publisher(MarkerArray, '/virtual_obstacles', 10)
        self.timer = self.create_timer(1.0, self.publish_trees)

    def publish_trees(self):
        marker_array = MarkerArray()
        
        # Example: Spawning a virtual tree at Coordinates [X: 5.0, Y: 4.0]
        tree = Marker()
        tree.header.frame_id = "map" # Locks the tree to the global map
        tree.id = 0
        tree.type = Marker.CYLINDER # Foxglove will draw a 3D cylinder
        tree.action = Marker.ADD
        
        # Position
        tree.pose.position.x = 5.0
        tree.pose.position.y = 4.0
        tree.pose.position.z = 1.0  # Center of the cylinder is 1m off the ground
        
        # Dimensions (1 meter thick, 2 meters tall)
        tree.scale.x = 1.0 
        tree.scale.y = 1.0
        tree.scale.z = 2.0 
        
        # Color (RGBA: Neon Green)
        tree.color.r = 0.2
        tree.color.g = 0.8
        tree.color.b = 0.2
        tree.color.a = 0.9 # Slightly transparent hologram look

        marker_array.markers.append(tree)
        self.publisher.publish(marker_array)
        self.get_logger().info("Spawning Virtual Trees to Foxglove...")

def main(args=None):
    rclpy.init(args=args)
    node = VirtualLandscape()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**2. How to view them:**
While your ROS simulation is running, execute `python3 spawn_virtual_trees.py` in a separate terminal. Open your Foxglove 3D Panel, open the topic list, and turn on `/virtual_obstacles`. Majestic green 3D cylinders will instantly pop up on the field!

---

## Step 3: Visualizing the Intended "Snake" Path
Investors want to see the "AI thinking". 

In our Autopilot script (`mower_action_client.py`), we already calculate the mathematical coordinates of the Boustrophedon snake BEFORE the tractor starts moving. 

**Implementation Idea:** 
We will add a few lines of code to `mower_action_client.py` to publish a `nav_msgs/Path` message containing those math coordinates. When Foxglove listens to this `/intended_path` topic, it automatically draws a glowing neon line connecting all the points. 

This guarantees the investors physically see the brilliance of the coverage algorithm drawn out on the tablet *before* the tractor even begins executing the mission.
