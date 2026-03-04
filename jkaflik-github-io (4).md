[Skip to content](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html#VPContent)

On this page

# Map server [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#frontmatter-title)

## Overview [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#overview)

Map server is a ROS node responsible for managing map and providing map-related services to navigation stack.

Such as:

- map persistence as a GeoJSON file
- adding and removing areas or docking stations
- publishing map
- publishing costmap grid for navigation stack
- publishing helper topics for visualization

Map provides a static 2D environment representation used for robot navigation. The main concept is to have a map that consists of a set of areas. Map is created by combining multiple areas together. Obstacle areas are decoupled from navigation areas and can be added or removed at any time.

The second concept is a pose of docking station. It consists of a position and orientation. Position is a middle of the charging connectors. Orientation heading towards the robot's connectors.

It is a drop-in replacement for [nav2 map server](https://navigation.ros.org/configuration/packages/configuring-map-server.html).

### ROS message definition [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#ros-message-definition)

msg

```
std_msgs/Header header
Area[] areas
DockingStation[] docking_stations
```

## Area [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#area)

Each area is a polygon that can be either free to navigate or occupied by an obstacle. It's uniquely identified by an ID. Area can be added, removed or updated at any time.

Area name is used to identify the area. It's not required to be unique, but it's recommended to use unique names to avoid confusion.

### Types [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#types)

- **Exclusion area** is an area that is not allowed to be occupied by the robot. It is used to exclude areas that are not safe for the robot to drive on. For example, a pond or a flower bed.
- **Navigation area** is an area that is allowed to be occupied by the robot. It is used to define the area where the robot is allowed to drive on. For example, a driveway.
- **Operation area** is an area that is allowed to be occupied by the robot. It is used to define the area where the robot is allowed to drive on and execute its operation - mowing a lawn.

### ROS message definition [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#ros-message-definition-1)

msg

```
# Definition of the area
# The area is defined by a polygon
# The area can be of 3 types:
# - Exclusion: the area is forbidden
# - Navigation: the area is a navigation area
# - Operation: the area is an operation area (e.g. lawn mowing area)

uint8 TYPE_EXCLUSION = 0
uint8 TYPE_NAVIGATION = 1
uint8 TYPE_OPERATION = 2

string id # id of the area
string name # name of the area
uint8 type # type of the area. 0 = obstacle, 1 = navigation, 2 = operation
geometry_msgs/PolygonStamped area # area of the zone
```

## Docking station [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#docking-station)

Docking station is a position where the robot can charge its batteries. It's uniquely identified by an ID. Docking station can be added, removed or updated at any time.

Pose is a position and orientation of the docking station. Position is a middle of the charging connectors. Orientation heading towards the robot's connectors.

### ROS message definition [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#ros-message-definition-2)

msg

```
string id # id of the docking station
string name # name of the docking station
geometry_msgs/PoseStamped pose # Usually a middle of the charging connectors. Orientation heading towards the robot's connectors.
```

## Map management API [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#map-management-api)

Area and docking station can be added, removed or updated at any time. All operations are performed using ROS services. After each operation, the map is published to the `/map` topic and persisted.

### Services [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#services)

#### Save area `/save_area` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#save-area-save-area)

srv

```
Area area
---
# Result
uint16 CODE_SUCCESS = 0
uint16 CODE_INVALID_AREA = 1
uint16 CODE_SAVE_FAILED = 2
uint16 CODE_UNKNOWN_ERROR = 99

uint16 code                # 0 is success, otherwise is error code
string message             # Information message
```

#### Remove area `/remove_area` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#remove-area-remove-area)

srv

```
string id # id of the docking station
---
# Result
uint16 CODE_SUCCESS = 0
uint16 CODE_NOT_FOUND = 1
uint16 CODE_UNKNOWN_ERROR = 99

uint16 code                # 0 is success, otherwise is error code
string message             # Information message
```

#### Save docking station `/save_docking_station` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#save-docking-station-save-docking-station)

srv

```
DockingStation docking_station
---
# Result
uint16 CODE_SUCCESS = 0
uint16 CODE_INVALID_DOCKING_STATION = 1
uint16 CODE_SAVE_FAILED = 2
uint16 CODE_UNKNOWN_ERROR = 99

uint16 code                # 0 is success, otherwise is error code
string message             # Information message
```

#### Remove docking station `/remove_docking_station` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#remove-docking-station-remove-docking-station)

srv

```
string id
---
# Result
uint16 CODE_SUCCESS = 0
uint16 CODE_NOT_FOUND = 1
uint16 CODE_REMOVE_FAILED = 2
uint16 CODE_UNKNOWN_ERROR = 99

uint16 code                # 0 is success, otherwise is error code
string message             # Information message
```

## Supported map types [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#supported-map-types)

### GeoJSON [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#geojson)

Currently the only supported map type is GeoJSON. It's a format for encoding a variety of geographic data structures. It's a human-readable and easy to parse format. OpenMowerNext uses a `Feature` of `polygon` type objects to represent areas and docking stations.

Map server will automatically load the map from the file specified in the `OM_MAP_PATH` environment variable:

bash

```
OM_MAP_PATH=$HOME/.openmower/map.geojson
```

#### Schema Definition [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#schema-definition)

OpenMowerNext extends the standard GeoJSON format with specific properties and conventions. A formal JSONSchema definition is available at [geojson-schema.json](https://jkaflik.github.io/OpenMowerNext/architecture/assets/geojson-schema.json) that documents:

- Area features (Polygon type) with navigation, operation, or exclusion types
- Docking station features (LineString type) with position and orientation information

#### Examples [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-server.html\#examples)

- [test\_map.geojson](https://github.com/jkaflik/OpenMowerROS2/src/map_server/test/test_map.geojson)