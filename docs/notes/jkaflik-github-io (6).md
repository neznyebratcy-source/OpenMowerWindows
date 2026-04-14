[Skip to content](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html#VPContent)

On this page

# Map recorder [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#frontmatter-title)

## Overview [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#overview)

Map recorder is a ROS node exposing an API to trigger map recording:

- record area boundary
- record docking station

Mower operator is responsible of controlling the robot. Publish twist commands to `/cmd_vel_joy` topic to control the robot.

WARNING

The robot must be in a known position. GPS should be using RTK corrections. Otherwise, the robot will not be able to record the area correctly. Expected accuracy is <2cm. Map recorder will not deny recording if GPS is not using RTK corrections, but the recorded area will be inaccurate.

IMPORTANT

Since robot's orientation is not known on startup, it is required to drive the robot around, spin it around and do a few circles to get an accurate orientation. Best to start moving in a straight line and do a few circles.

## Area boundary recording [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#area-boundary-recording)

User initiates area boundary recording by calling `/record_area_boundary` action. It can be started in two modes:

| Recording Mode | Description |
| --- | --- |
| `auto_recording = false` | User manually adds points to the area boundary |
| `auto_recording = true` | User drives the robot around the area and the area boundary is recorded automatically |

Auto recording can be enabled/disabled at any time using `/set_recording_mode` action.

Auto recording is useful for areas that are not bounded with a straight line with a lot of curves. If your area is a rectangle or a simple shape, it's better to use manual recording.

User can add points to the area boundary by calling `/add_boundary_point` action. The point is added to the area boundary and the area is updated. The area is not saved to the map server yet. It is only saved when the recording is finished.

Recorded polygon is published to `/map_recorder/record_boundaries_polygon` topic. It can be used for visualization purposes.

Recording is finished by calling `/finish_area_recording` action. The area is saved to the map server and immidiately available for use.

## Docking station recording [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#docking-station-recording)

Drive the robot in a front of the docking station and call `/record_docking_station` action. It will start docking station recording. Mower will automatically drive to the docking station.

If charging is detected, the docking station will be recorded with it's pose. (mower's `charging_port` rotated by 180 degrees)

If charging is not detected, action will be aborted and the docking station will not be recorded.

## Actions [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#actions)

### Record area boundary `/record_area_boundary` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#record-area-boundary-record-area-boundary)

action

```
# Goal
string name
uint8 type # type of the area. 0 = obstacle, 1 = navigation, 2 = operation
bool auto_recording        # Whether to record points automatically
float64 distance_threshold # Minimum distance between recorded points in auto mode (defaults to 5cm)
---
# Result
uint16 CODE_SUCCESS = 0
uint16 CODE_INVALID_POLYGON = 1
uint16 CODE_TOO_FEW_POINTS = 2
uint16 CODE_SERVICE_UNAVAILABLE = 3
uint16 CODE_SERVICE_FAILED = 4
uint16 CODE_CANCELED = 5
uint16 CODE_UNKNOWN_ERROR = 99

uint16 code                # 0 is success, otherwise is error code
string message             # Information message
Area area                  # The recorded area
---
# Feedback

uint16 STATUS_NONE = 0
uint16 STATUS_RECORDING = 1
uint16 STATUS_PROCESSING = 2
uint16 STATUS_SAVING = 3
uint16 STATUS_ERROR = 99

uint16 status              # Current status of recording
string message             # Information message
uint32 point_count         # Number of points recorded so far
geometry_msgs/PolygonStamped area # area of the zone
```

#### Set recording mode `/set_recording_mode` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#set-recording-mode-set-recording-mode)

srv

```
bool data # e.g. true for auto recording mode
---
bool success   # indicate successful run of triggered service
string message # informational, e.g. for error messages
```

#### Add boundary point `/add_boundary_point` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#add-boundary-point-add-boundary-point)

srv

```
---
bool success   # indicate successful run of triggered service
string message # informational, e.g. for error messages
```

#### Finish area recording `/finish_area_recording` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#finish-area-recording-finish-area-recording)

srv

```
---
bool success   # indicate successful run of triggered service
string message # informational, e.g. for error messages
```

* * *

### Record docking station `/record_docking_station` [​](https://jkaflik.github.io/OpenMowerNext/architecture/map-recorder.html\#record-docking-station-record-docking-station)

action

```
# Goal
string name  # Name for the docking station
---
# Result
uint16 CODE_SUCCESS = 0
uint16 CODE_NO_CHARGING_DETECTED = 1
uint16 CODE_POOR_LOCALIZATION = 2
uint16 CODE_SERVICE_UNAVAILABLE = 3
uint16 CODE_SERVICE_FAILED = 4
uint16 CODE_CANCELED = 5
uint16 CODE_DRIVE_FAILURE = 6
uint16 CODE_UNKNOWN_ERROR = 99

uint16 code                # 0 is success, otherwise is error code
string message             # Information message
DockingStation docking_station  # The recorded docking station
---
# Feedback
uint16 STATUS_NONE = 0
uint16 STATUS_DRIVING = 1
uint16 STATUS_WAITING_FOR_CHARGING = 2
uint16 STATUS_RECORDING = 3
uint16 STATUS_SAVING = 4
uint16 STATUS_ERROR = 99

uint16 status              # Current status of recording
string message             # Information message
```