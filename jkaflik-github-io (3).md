[Skip to content](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html#VPContent)

On this page

# Robot localization [​](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html\#frontmatter-title)

## Overview [​](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html\#overview)

Robot pose is based on an absolute position from GPS and relative readings from wheel odometry and IMU. Orientation is not known on startup and defaults to 0.

As soon as robot starts moving, orientation is assumed based on robot motion and sensors reading. It might take a while to get an accurate orientation. Best to start moving in a straight line and do a few circles.

Currently, there is no fallback scenario if had its position changed externally. For example, if you move the robot manually, it will not be able to recover position itself. It will require same procedure as on startup.

Later on, when undocking behavior is implemented, it will be possible to recover orientation knowing base station position.

## Sensors [​](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html\#sensors)

[robot\_localization documentation](http://docs.ros.org/en/melodic/api/robot_localization/html/integrating_gps.html) nicely describes how to get wheel odometry, GPS and IMU sensors data fusion to get an accurate localization.

![Senor data flow](http://docs.ros.org/en/melodic/api/robot_localization/html/_images/navsat_transform_workflow.png)

### Wheel odometry [​](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html\#wheel-odometry)

Default motor controller VESC reports wheel odometry.

### IMU [​](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html\#imu)

Accelerometer and gyroscope is required. Magnetometer is not fused.

### GPU [​](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html\#gpu)

It's expected GPS is RTK capable. Otherwise, localization will be inaccurate. More on this in [GPS](https://jkaflik.github.io/OpenMowerNext/gps.html) section.

## Configuration [​](https://jkaflik.github.io/OpenMowerNext/architecture/localization.html\#configuration)

yaml

```
ekf_se_odom:
  ros__parameters:
    frequency: 50.0
    sensor_timeout: 0.025
    two_d_mode: true
    transform_time_offset: 0.0
    transform_timeout: 0.0
    print_diagnostics: true
    debug: false

    map_frame: map
    odom_frame: odom
    base_link_frame: base_link
    world_frame: odom

    #x     , y     , z,
    #roll  , pitch , yaw,
    #vx    , vy    , vz,
    #vroll , vpitch, vyaw,
    #ax    , ay    , az

    odom0: diff_drive_base_controller/odom
    odom0_config: [false, false, false,\
                   false, false, false,\
                   true,  true,  true,\
                   false, false, true,\
                   false, false, false]
    odom0_queue_size: 50
    odom0_nodelay: true
    odom0_differential: false
    odom0_relative: false

    imu0: imu/data
    imu0_config: [false, false, false,\
                  true,  true,  false,\
                  false, false, false,\
                  true,  true,  true,\
                  true,  true,  true]
    imu0_nodelay: false
    imu0_differential: false
    imu0_relative: false
    imu0_queue_size: 100
    imu0_remove_gravitational_acceleration: true

    use_control: false

    process_noise_covariance: [1.0e-3, 0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    1e-3, 0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    1e-3, 0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.3,  0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.3,  0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.01, 0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.5,   0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.5,   0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.1,  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.3,  0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.3,  0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.3,  0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.3,  0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.3,  0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.3]

    initial_estimate_covariance: [1e-9, 0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    1e-9, 0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    1e-9, 0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    1.0,  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    1.0,  0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    1e-9, 0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    1.0,  0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    1.0,  0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    1.0,  0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    1.0,   0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     1.0,   0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     1.0,   0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     1.0,  0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    1.0,  0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    1.0]

ekf_se_map:
  ros__parameters:
    frequency: 50.0
    sensor_timeout: 0.1
    two_d_mode: true
    transform_time_offset: 0.0
    transform_timeout: 0.0
    print_diagnostics: true
    debug: false

    map_frame: map
    odom_frame: odom
    base_link_frame: base_link
    world_frame: map

    #x     , y     , z,§
    #roll  , pitch , yaw,
    #vx    , vy    , vz,
    #vroll , vpitch, vyaw,
    #ax    , ay    , az

    odom0: diff_drive_base_controller/odom
    odom0_config: [false, false, false,\
                   false, false, false,\
                   true,  true,  true,\
                   false, false, true,\
                   false, false, false]
    odom0_queue_size: 10
    odom0_nodelay: true
    odom0_differential: false
    odom0_relative: false

    odom1: odometry/gps
    odom1_config: [true,  true,  false,\
                   false, false, false,\
                   false, false, false,\
                   false, false, false,\
                   false, false, false]
    odom1_queue_size: 10
    odom1_nodelay: true
    odom1_differential: false
    odom1_relative: false

    imu0: imu/data
    imu0_config: [false, false, false,\
                  true,  true,  false,\
                  false, false, false,\
                  true,  true,  true,\
                  true,  true,  true]
    imu0_nodelay: true
    imu0_differential: false
    imu0_relative: false
    imu0_queue_size: 10
    imu0_remove_gravitational_acceleration: true

    use_control: false

    process_noise_covariance: [1.0,  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    1.0,  0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    1e-3, 0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.3,  0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.3,  0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.3, 0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.5,   0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.5,   0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.1,  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.3,  0.0,    0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.3,  0.0,    0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.3,  0.0,    0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.3,  0.0,    0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.3,  0.0,\
                               0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.3]

    initial_estimate_covariance: [1.0,  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    1.0,  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    1e-9, 0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    1.0,  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    1.0,  0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    1e-9, 0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    1.0,  0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    1.0,  0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    1.0,  0.0,     0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    1.0,   0.0,     0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     1.0,   0.0,     0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     1.0,   0.0,    0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     1.0,  0.0,    0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    1.0,  0.0,\
                                  0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,    0.0,     0.0,     0.0,     0.0,    0.0,    1.0]

navsat_transform_node:
  ros__parameters:
    frequency: 30.0
    delay: 3.0
    zero_altitude: true
    publish_filtered_gps: true
    wait_for_datum: true
    use_odometry_yaw: true
    use_local_cartesian: true
```