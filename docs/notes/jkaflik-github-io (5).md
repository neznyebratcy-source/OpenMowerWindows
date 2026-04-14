[Skip to content](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html#VPContent)

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

- [Overview](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html#overview "Overview")
- [Docking Station Information](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html#docking-station-information "Docking Station Information")
- [Services](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html#services "Services")
- [Actions](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html#actions "Actions")
- [Implementation Details](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html#implementation-details "Implementation Details")

# Docking helper [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#frontmatter-title)

## Overview [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#overview)

Dock Helper is a ROS node providing services and actions to assist with docking the robot to charging stations. It manages:

- Finding the nearest docking station
- Docking to a specific docking station by ID
- Docking to the nearest available docking station

The node obtains docking station information from the map and uses the Nav2 docking capability to execute the actual docking operation.

IMPORTANT

The node requires transform information between the robot's `base_link` and `charging_port` to calculate the correct approach position for docking.

## Docking Station Information [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#docking-station-information)

Docking stations are received from the `/mowing_map` topic and stored internally. Each docking station includes:

- ID
- Name
- Pose (position and orientation)

## Services [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#services)

### Find Nearest Docking Station `/find_nearest_docking_station` [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#find-nearest-docking-station-find-nearest-docking-station)

This service finds the docking station closest to the robot's current position and returns its details.

srv

```
---
# Result
uint16 CODE_SUCCESS = 0
uint16 CODE_NOT_FOUND = 1
uint16 CODE_UNKNOWN_ERROR = 99

DockingStation docking_station
uint16 code                # 0 is success, otherwise is error code
string message             # Information message
```

## Actions [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#actions)

### Dock Robot to Nearest Station `/dock_robot_nearest` [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#dock-robot-to-nearest-station-dock-robot-nearest)

action

```
# goal definition
---
# Result codes
uint16 CODE_SUCCESS = 0
uint16 CODE_DOCK_NOT_IN_DB = 901
uint16 CODE_DOCK_NOT_VALID = 902
uint16 CODE_FAILED_TO_STAGE = 903
uint16 CODE_FAILED_TO_DETECT_DOCK = 904
uint16 CODE_FAILED_TO_CONTROL = 905
uint16 CODE_FAILED_TO_CHARGE = 906
uint16 CODE_UNKNOWN = 999

DockingStation chosen_docking_station
uint16 code                # 0 is success, otherwise is error code
string message             # Information message
uint16 num_retries         # Number of retries attempted
---
# Feedback
# Status codes
uint16 STATUS_NONE = 0
uint16 STATUS_NAV_TO_STAGING_POSE = 1
uint16 STATUS_INITIAL_PERCEPTION = 2
uint16 STATUS_CONTROLLING = 3
uint16 STATUS_WAIT_FOR_CHARGE = 4
uint16 STATUS_RETRY = 5

DockingStation chosen_docking_station
uint16 status              # Current status of docking process
string message             # Information message
uint16 num_retries         # Number of retries attempted
builtin_interfaces/Duration docking_time  # Docking time elapsed
```

### Dock Robot to Specific Station `/dock_robot_to` [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#dock-robot-to-specific-station-dock-robot-to)

action

```
# goal definition
string dock_id
---
# Result codes
uint16 CODE_SUCCESS = 0
uint16 CODE_DOCK_NOT_IN_DB = 901
uint16 CODE_DOCK_NOT_VALID = 902
uint16 CODE_FAILED_TO_STAGE = 903
uint16 CODE_FAILED_TO_DETECT_DOCK = 904
uint16 CODE_FAILED_TO_CONTROL = 905
uint16 CODE_FAILED_TO_CHARGE = 906
uint16 CODE_UNKNOWN = 999

DockingStation chosen_docking_station
uint16 code                # 0 is success, otherwise is error code
string message             # Information message
uint16 num_retries         # Number of retries attempted
---
# Feedback
# Status codes
uint16 STATUS_NONE = 0
uint16 STATUS_NAV_TO_STAGING_POSE = 1
uint16 STATUS_INITIAL_PERCEPTION = 2
uint16 STATUS_CONTROLLING = 3
uint16 STATUS_WAIT_FOR_CHARGE = 4
uint16 STATUS_RETRY = 5

DockingStation chosen_docking_station
uint16 status              # Current status of docking process
string message             # Information message
uint16 num_retries         # Number of retries attempted
builtin_interfaces/Duration docking_time  # Docking time elapsed
```

## Implementation Details [​](https://jkaflik.github.io/OpenMowerNext/architecture/docking-helper.html\#implementation-details)

The docking operation utilizes Nav2's `/dock_robot` action to perform the actual docking. The Docking Helper node:

1. Identifies the target docking station (nearest or specific)
2. Calculates the appropriate docking pose by accounting for the offset between the robot's `base_link` and `charging_port`
3. Monitors docking progress and reports status through action feedback
4. Reports success or failure when docking completes

The docking pose is calculated by:

- Taking the docking station's pose
- Rotating it 180 degrees (to face the docking station)
- Adding an offset based on the distance between `base_link` and `charging_port`

Pager

[Previous pageMap recorder](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html)

[Next pageSim node](https://jkaflik.github.io/OpenMowerNext/architecture/sim-node.html)