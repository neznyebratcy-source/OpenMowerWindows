# Implementation Guide: Dynamic Obstacle Avoidance (Orchard Demo)

This guide provides the exact code modifications necessary to upgrade the "blind" OpenMower configuration into a fully autonomous, obstacle-dodging system for the simulation demo. 

By completing this guide, the virtual tractor will mathematically detect physical trees in Gazebo using simulated lasers and gracefully weave around them in real-time.

---

## Step 1: Give the Tractor "Eyes" (The 2D Lidar)

We must attach a virtual laser scanner to the physical model of the tractor so Gazebo can project rays and calculate collisions.

**File to modify:** `description/robot_core.xacro`

Scroll to the bottom of the file (just above the closing `</robot>` tag) and insert the Lidar joint, link, and Gazebo plugin:

```xml
    <!-- VIRTUAL LIDAR FOR OBSTACLE AVOIDANCE -->
    <joint name="laser_joint" type="fixed">
        <parent link="chassis"/>
        <child link="laser_frame"/>
        <!-- Mount sensor on the front bumper -->
        <origin xyz="${chassis_length} 0.0 ${chassis_height}" rpy="0 0 0"/>
    </joint>

    <link name="laser_frame">
        <visual>
            <geometry>
                <cylinder radius="0.05" length="0.05"/>
            </geometry>
            <material name="black"/>
        </visual>
    </link>

    <gazebo reference="laser_frame">
        <!-- The Gazebo GPU Lidar Plugin -->
        <sensor name="lidar" type="gpu_lidar">
            <always_on>true</always_on>
            <visualize>true</visualize> <!-- Draws red lasers in Gazebo -->
            <update_rate>10</update_rate>
            <ray>
                <scan>
                    <horizontal>
                        <samples>360</samples>
                        <resolution>1.0</resolution>
                        <min_angle>-3.14159</min_angle>
                        <max_angle>3.14159</max_angle>
                    </horizontal>
                </scan>
                <range>
                    <min>0.15</min>
                    <max>10.0</max>
                </range>
            </ray>
            <topic>/scan</topic>
            <plugin name="gz::sim::systems::Sensors" filename="libgz-sim-sensors-system.so"/>
        </sensor>
    </gazebo>
```

**File to modify:** `launch/sim.launch.py`
In the `ros_gz_bridge` arguments block (around line 57), you must forward this new laser data to ROS 2:
```python
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # ... keep existing lines ...
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        output='screen'
    )
```

---

## Step 2: Upgrade the AI Brain (Nav2 Costmaps)

Currently, Nav2 only looks at static map boundaries. We need to add the `ObstacleLayer` to tell the AI to dynamically avoid objects appearing in the `/scan` laser topic.

**File to modify:** `config/nav2_params.yaml`

1. Under `local_costmap: local_costmap: ros__parameters: plugins:` (Line ~79), change it to:
```yaml
      plugins: ["obstacle_layer", "static_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        enabled: True
        observation_sources: scan
        scan:
          topic: /scan
          max_obstacle_height: 2.0
          clearing: True
          marking: True
          data_type: "LaserScan"
```

2. Do the exact same thing for the `global_costmap` plugins (Line ~97):
```yaml
      plugins: ["obstacle_layer", "static_layer"]
      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        # ... (same settings as above)
```

---

## Step 3: Plant the Virtual Forest

Now that the tractor can see, we need to give it something to look at. We will spawn physical "trees" (cylinders) inside the Gazebo world. 

**File to modify:** `worlds/empty.sdf`

Inside the `<world name="map">` tag (at the bottom, just above `</world>`), paste this code to spawn a Solid Tree:

```xml
        <!-- TREE 1 -->
        <model name='tree_1'>
            <pose>3.0 1.5 1.0 0 0 0</pose> <!-- Change coordinates to put it in the mower's path! -->
            <link name='link'>
                <collision name='collision'>
                    <geometry>
                        <cylinder><radius>0.2</radius><length>2</length></cylinder>
                    </geometry>
                </collision>
                <visual name='visual'>
                    <geometry>
                        <cylinder><radius>0.2</radius><length>2</length></cylinder>
                    </geometry>
                    <material>
                        <ambient>0.2 0.8 0.2 1</ambient> <!-- Green color -->
                        <diffuse>0.2 0.8 0.2 1</diffuse>
                    </material>
                </visual>
            </link>
            <static>true</static>
        </model>
```
*(You can copy and paste this block multiple times, changing the `<pose>` coordinates to build a row of trees like an orchard).*

---

## Execution
Run `docker compose up --build`. You will physically see the trees in the Gazebo window, and you will see red lasers bouncing off them. When you run your Action Client, the glowing Nav2 path will dramatically snake around the green trees!
