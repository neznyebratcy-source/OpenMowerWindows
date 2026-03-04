[Skip to content](https://jkaflik.github.io/OpenMowerNext/simulator.html#VPContent)

On this page

# Simulator [​](https://jkaflik.github.io/OpenMowerNext/simulator.html\#simulator)

## Overview [​](https://jkaflik.github.io/OpenMowerNext/simulator.html\#overview)

OpenMowerNext incorporates a [Gazebo](http://gazebosim.org/) simulator and [ros\_gz](https://github.com/gazebosim/ros_gz) integration.

TIP

If you are not familiar with Gazebo, please refer to [Gazebo tutorials](http://gazebosim.org/tutorials).

WARNING

This project uses Gazebo Fortress. Formerly known as Ignition Fortress.

![Robot simulation](https://jkaflik.github.io/OpenMowerNext/assets/gazebo.B-qVzh7e.jpg)

## Getting started [​](https://jkaflik.github.io/OpenMowerNext/simulator.html\#getting-started)

Run the following command to start the simulator:

bash

```
ros2 launch openmower sim.launch.py
```

If run inside [devcontainer](https://jkaflik.github.io/OpenMowerNext/devcontainer.html), Gazebo GUI will be displayed in a VNC web client. You can access it by opening [`http://localhost:12345`](http://localhost:12345/) in your browser.

TIP

Learn more about [VNC client](https://jkaflik.github.io/OpenMowerNext/devcontainer.html#detailed).

It's possible to run the simulator with GUI on external host machine. I haven't done it myself since GUI is unstable on MacOS.

## Current state [​](https://jkaflik.github.io/OpenMowerNext/simulator.html\#current-state)

- ✅ Robot model
- ✅ ros2\_control controller
- ✅ GPS sensor
- ✅ IMU sensor
- ✅ Emulate OpenMowerNext firmware (charging and battery) using [sim node](https://jkaflik.github.io/OpenMowerNext/architecture/sim-node.html)

## World definition [​](https://jkaflik.github.io/OpenMowerNext/simulator.html\#world-definition)

xml

```
<?xml version="1.0" ?>
<sdf version="1.8">
    <world name="map">
        <physics name="1ms" type="ignored">
            <max_step_size>0.001</max_step_size>
            <real_time_factor>1.0</real_time_factor>
        </physics>

        <plugin filename="libgz-sim-physics-system.so" name="gz::sim::systems::Physics">
        </plugin>
        <plugin filename="libgz-sim-user-commands-system.so" name="gz::sim::systems::UserCommands">
        </plugin>
        <plugin filename="libgz-sim-scene-broadcaster-system.so" name="gz::sim::systems::SceneBroadcaster">
        </plugin>

        <plugin filename="libgz-sim-navsat-system" name="gz::sim::systems::NavSat">
        </plugin>
        <plugin filename="libgz-sim-imu-system.so" name="gz::sim::systems::Imu">
        </plugin>

        <spherical_coordinates>
            <surface_model>EARTH_WGS84</surface_model>
            <world_frame_orientation>ENU</world_frame_orientation>
            <latitude_deg>-22.9</latitude_deg>
            <longitude_deg>-43.2</longitude_deg>
            <elevation>0</elevation>
            <heading_deg>0</heading_deg>
        </spherical_coordinates>

        <!-- Add sun light with shadows -->
        <light type="directional" name="sun">
            <cast_shadows>true</cast_shadows>
            <pose>0 0 10 0 0 0</pose>
            <diffuse>0.8 0.8 0.8 1</diffuse>
            <specular>0.2 0.2 0.2 1</specular>
            <direction>-0.5 0.1 -0.9</direction>
        </light>

        <!-- OpenMower Docking Station -->
        <model name="docking_station">
            <static>true</static>
            <pose>1.5 1.5 0 0 0 0</pose>

            <!-- Add pose publisher plugin -->
            <plugin filename="libgz-sim-pose-publisher-system.so" name="gz::sim::systems::PosePublisher">
                <publish_link_pose>true</publish_link_pose>
                <publish_nested_model_pose>true</publish_nested_model_pose>
                <update_frequency>1</update_frequency>
                <!-- Charging contact is positioned at [0.32, 0, 0.06] relative to docking station origin -->
            </plugin>

            <!-- Base Plate -->
            <link name="base_plate">
                <visual name="visual">
                    <geometry>
                        <box>
                            <size>0.8 0.4 0.01</size>
                        </box>
                    </geometry>
                    <material>
                        <ambient>0.1 0.1 0.1 1</ambient>
                        <diffuse>0.1 0.1 0.1 1</diffuse>
                        <specular>0.01 0.01 0.01 1</specular>
                    </material>
                </visual>
                <collision name="collision">
                    <geometry>
                        <box>
                            <size>0.8 0.4 0.01</size>
                        </box>
                    </geometry>
                </collision>
            </link>

            <!-- Charging Port -->
            <link name="charging_port">
                <pose>0.35 0 0.075 0 0 0</pose>
                <visual name="visual">
                    <geometry>
                        <box>
                            <size>0.1 0.3 0.15</size>
                        </box>
                    </geometry>
                    <material>
                        <ambient>0.1 0.1 0.1 1</ambient>
                        <diffuse>0.1 0.1 0.1 1</diffuse>
                        <specular>0.01 0.01 0.01 1</specular>
                    </material>
                </visual>
                <collision name="collision">
                    <geometry>
                        <box>
                            <size>0.1 0.3 0.15</size>
                        </box>
                    </geometry>
                </collision>

            </link>

            <!-- Charging Contact - Modified for better visibility -->
            <link name="charging_contact">
                <pose>0.32 0 0.06 0 0 0</pose>
                <visual name="visual">
                    <geometry>
                        <box>
                            <size>0.02 0.15 0.03</size>
                        </box>
                    </geometry>
                    <material>
                        <ambient>1.0 0.0 0.0 1</ambient>
                        <diffuse>1.0 0.0 0.0 1</diffuse>
                        <specular>1.0 1.0 1.0 1</specular>
                        <emissive>0.5 0.0 0.0 1</emissive>
                    </material>
                </visual>
                <collision name="collision">
                    <geometry>
                        <box>
                            <size>0.02 0.15 0.03</size>
                        </box>
                    </geometry>
                </collision>
            </link>

            <!-- Guide Rail Left -->
            <link name="guide_rail_left">
                <pose>0.15 0.2 0.02 0 0 0</pose>
                <visual name="visual">
                    <geometry>
                        <box>
                            <size>0.4 0.02 0.04</size>
                        </box>
                    </geometry>
                    <material>
                        <ambient>0.3 0.3 0.3 1</ambient>
                        <diffuse>0.3 0.3 0.3 1</diffuse>
                        <specular>0.1 0.1 0.1 1</specular>
                    </material>
                </visual>
                <collision name="collision">
                    <geometry>
                        <box>
                            <size>0.4 0.02 0.04</size>
                        </box>
                    </geometry>
                </collision>
            </link>

            <!-- Guide Rail Right -->
            <link name="guide_rail_right">
                <pose>0.15 -0.2 0.02 0 0 0</pose>
                <visual name="visual">
                    <geometry>
                        <box>
                            <size>0.4 0.02 0.04</size>
                        </box>
                    </geometry>
                    <material>
                        <ambient>0.3 0.3 0.3 1</ambient>
                        <diffuse>0.3 0.3 0.3 1</diffuse>
                        <specular>0.1 0.1 0.1 1</specular>
                    </material>
                </visual>
                <collision name="collision">
                    <geometry>
                        <box>
                            <size>0.4 0.02 0.04</size>
                        </box>
                    </geometry>
                </collision>
            </link>

            <!-- Fixed joints for connecting parts -->
            <joint name="base_to_charging_port" type="fixed">
                <parent>base_plate</parent>
                <child>charging_port</child>
            </joint>

            <joint name="charging_port_to_contact" type="fixed">
                <parent>charging_port</parent>
                <child>charging_contact</child>
            </joint>

            <!-- Joints for guide rails -->
            <joint name="base_to_guide_rail_left" type="fixed">
                <parent>base_plate</parent>
                <child>guide_rail_left</child>
            </joint>

            <joint name="base_to_guide_rail_right" type="fixed">
                <parent>base_plate</parent>
                <child>guide_rail_right</child>
            </joint>
        </model>

        <include>
            <uri>
                https://fuel.gazebosim.org/1.0/hexarotor/models/grasspatch
            </uri>
        </include>
    </world>
</sdf>
```