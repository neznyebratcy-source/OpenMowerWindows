[Skip to content](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html#VPContent)

[OpenMowerNext](https://jkaflik.github.io/OpenMowerNext/)

Search`` `K`

Main Navigation [Home](https://jkaflik.github.io/OpenMowerNext/) [Documentation](https://jkaflik.github.io/OpenMowerNext/getting-started.html)

[github](https://github.com/jkaflik/OpenMowerNext)[discord](https://discord.gg/jE7QNaSxW7)

Appearance

[github](https://github.com/jkaflik/OpenMowerNext)[discord](https://discord.gg/jE7QNaSxW7)

Menu

On this page

Sidebar Navigation

[**Getting started**](https://jkaflik.github.io/OpenMowerNext/getting-started.html)

[Roadmap](https://jkaflik.github.io/OpenMowerNext/roadmap.html)

## Architecture

[ROS workspace](https://jkaflik.github.io/OpenMowerNext/architecture/ros-workspace.html)

[Mainboard firmware](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html)

[Robot localization](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html)

[Map server](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html)

[Map recorder](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html)

[Docking helper](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html)

[Sim node](https://jkaflik.github.io/OpenMowerNext/architecture/sim-node.html)

[**Contributing guide**](https://jkaflik.github.io/OpenMowerNext/contributing.html)

[**Devcontainer**](https://jkaflik.github.io/OpenMowerNext/devcontainer.html)

[CLion alternative](https://jkaflik.github.io/OpenMowerNext/clion-env.html)

[Visualisation](https://jkaflik.github.io/OpenMowerNext/visualisation.html)

[Simulator](https://jkaflik.github.io/OpenMowerNext/simulator.html)

On this page

- [Overview](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html#overview "Overview")
- [Features](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html#features "Features")
- [Flash](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html#flash "Flash")

# OpenMowerNext firmware [​](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html\#openmowernext-firmware)

## Overview [​](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html\#overview)

Original OpenMower firmware is communicating with ROS via serial port using simple packet protocol. With ROS2 we can use more advanced communication protocols, like [DDS](https://en.wikipedia.org/wiki/Data_Distribution_Service), using [micro-ROS](https://micro.ros.org/). No need to run a dedicated node that translates serial packets to ROS messages. Micro-ROS takes care of that.

This firmware supports only the recent OpenMower mainboard v0.13.x.

## Features [​](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html\#features)

- ✅ DDS communication
- ✅ `sensor_msgs/Imu` message published on `/imu/data_raw` topic
- ✅ `sensor_msgs/BatteryState` message published on `/power` topic
  - ✅ `std_msgs/Float32` message published on `/power/charge_voltage` topic
  - ✅ `std_msgs/Bool` message published on `/power/charger_present` topic
- ✅ OpenMower charging logic
- ✅ ping micro-ROS agent, make sure it is alive
- 🔴 safety features

## Flash [​](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html\#flash)

Follow instructions in [omros2-firmware](https://github.com/jkaflik/omros2-firmware#build) repository.

Pager

[Previous pageROS workspace](https://jkaflik.github.io/OpenMowerNext/architecture/ros-workspace.html)

[Next pageRobot localization](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html)