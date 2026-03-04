[Skip to content](https://jkaflik.github.io/OpenMowerNext/architecture/ros-workspace.html#VPContent)

On this page

# ROS workspace [​](https://jkaflik.github.io/OpenMowerNext/architecture/ros-workspace.html\#ros-workspace)

## Overview [​](https://jkaflik.github.io/OpenMowerNext/architecture/ros-workspace.html\#overview)

ROS workspace is a directory where you can build and run ROS packages. It is a recommended way to organize your ROS projects. It's no different for OpenMowerNext. The root of the repository is a ROS workspace.

## Nodes [​](https://jkaflik.github.io/OpenMowerNext/architecture/ros-workspace.html\#nodes)

- [`map_server`](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html) \- a ROS node responsible for managing map and providing map-related services to navigation stack
- [`map_recorder`](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html) \- a ROS node responsible for recording map

## External packages [​](https://jkaflik.github.io/OpenMowerNext/architecture/ros-workspace.html\#external-packages)

There are few biggest chunks to mention:

- [ros2\_control](https://control.ros.org/master/index.html) \- differential drive controller, but also a hardware layer provider
- [nav2](https://navigation.ros.org/) \- navigation stack
- [robot\_localization](http://docs.ros.org/en/noetic/api/robot_localization/html/index.html) \- fuse sensors data to get accurate pose estimation
- [NTRIP client](https://github.com/LORD-MicroStrain/ntrip_client) \- a ROS node to connect to NTRIP caster and get RTK corrections
- [Foxglove bridge](https://foxglove.dev/docs/studio/connection/using-foxglove-bridge) \- a ROS node exposing websocket connection to Foxglove Studio. See instructions [here](https://jkaflik.github.io/OpenMowerNext/visualisation.html). It can be used for custom Web UIs as well.

Hardware specific packages:

- [VESC driver interface](https://github.com/sbgisen/vesc/tree/humble-devel) \- a ros2\_control hardware layer implementation for VESC motor controllers
- [ublox\_f9p](https://github.com/jkaflik/ublox_f9p) \- a ROS2 driver for u-blox F9P GNSS receiver with support of UBX protocol
- [micro-ros-agent](https://github.com/micro-ROS/micro-ROS-Agent) \- a micro-ROS agent to connect to micro-ROS nodes. It's used to connect to the [micro-ROS node running on the OpenMower mainboard](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html).