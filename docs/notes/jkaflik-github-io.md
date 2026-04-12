[Skip to content](https://jkaflik.github.io/OpenMowerNext/getting-started.html#VPContent)

On this page

# Getting started [​](https://jkaflik.github.io/OpenMowerNext/getting-started.html\#frontmatter-title)

Let's get started with a quick overview of the project.

WARNING

Project is in early development stage. Actual mower logic is missing and things are likely to change. The list of identified missing features can be found in GitHub [issues](https://github.com/jkaflik/OpenMowerNext/issues).

## Overview [​](https://jkaflik.github.io/OpenMowerNext/getting-started.html\#overview)

The purpose of this project is no different from original [OpenMower project ROS implementation](https://github.com/ClemensElflein/open_mower_ros). OpenMowerNext is build on top of [ROS2](https://index.ros.org/doc/ros2/) following all the best practices and recommendations.

At this stage of the project, only one intention to use it is contributing to the project. If you are interested in the project, please feel free to contribute. It was started as a learning project for myself, but I hope it will be useful for others as well.

## Abilities [​](https://jkaflik.github.io/OpenMowerNext/getting-started.html\#abilities)

INFO

This section is not complete yet. It will be updated as the project progresses.

- ✅ Control robot
- ✅ Localization
  - ✅ Odometry
  - ✅ IMU
  - ✅ GPS
- ✅ Simulation using Gazebo
- ✅ Map management
- ✏️ [Mower logic](https://github.com/jkaflik/OpenMowerNext/issues/9)
- ✏️ [Configuration](https://jkaflik.github.io/OpenMowerNext/configuration.html)
- ✏️ User interface

### Roadmap [​](https://jkaflik.github.io/OpenMowerNext/getting-started.html\#roadmap)

What was already said, the project is in early development stage. Please get familiar with [Roadmap](https://jkaflik.github.io/OpenMowerNext/roadmap.html) to get an idea of what is planned for the future.

## Requirements [​](https://jkaflik.github.io/OpenMowerNext/getting-started.html\#requirements)

Some of the instructions might be specific to my setup, but I will try to make it as generic as possible. Project is tested on YardForce Classic 500B model. It should work on other models supported by OpenMower as well, but it is not tested.

### Hardware [​](https://jkaflik.github.io/OpenMowerNext/getting-started.html\#hardware)

- [Setup as for OpenMower](https://openmower.de/docs/robot-assembly/prepare-the-parts/)
  - [OpenMower v0.13.x mainboard](https://openmower.de/docs/robot-assembly/prepare-the-parts/prepare-mainboard/) with [omros2-firmware](https://github.com/jkaflik/omros2-firmware) flashed. Learn more about the custom firmware in [omros2-firmware](https://jkaflik.github.io/OpenMowerNext/architecture/omros2-firmware.html).

### Software [​](https://jkaflik.github.io/OpenMowerNext/getting-started.html\#software)

- 64bit Linux (tested on Ubuntu 22.04)
- [ROS2 Jazzy](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)

or

There is no need to install ROS2 on your host machine. You can use [Docker](https://docs.docker.com/engine/install/) instead.

## Installation [​](https://jkaflik.github.io/OpenMowerNext/getting-started.html\#installation)

INFO

This section is not complete yet. It will be updated as the project progresses. If you are interested in the development, go to the [contributing guide](https://jkaflik.github.io/OpenMowerNext/contributing.html) to run the project.