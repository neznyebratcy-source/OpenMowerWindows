# Autonomous Tractor: MVP Architecture Vision
**Target:** End-of-April Investor Demo

To meet the aggressive one-month deadline and guarantee a flawless presentation in front of investors, we must adhere to the "Simplest MVP" (Minimum Viable Product) philosophy. The golden rule for hardware demos is: **Never rely on the internet.** 

This vision outlines the most robust, fail-proof architecture designed specifically to work flawlessly in any remote field condition.

---

## 1. Field Operations & Interface (The "Tablet App")
Building a custom tablet application from scratch would take months and introduce unseen bugs. We will bypass this entirely.

*   **On-Robot Execution (The "Brain"):** All mission-critical controls, safety layers, and the ROS 2 Autopilot (Nav2 + Coverage Path Planning algorithm) run completely locally on the tractor's integrated computer (Raspberry Pi/Jetson). The tractor is fully self-sufficient.
*   **The Operator Interface:** The driver’s tablet will run **Foxglove Studio** as the primary application. Foxglove is highly stable, already integrated into our ROS stack, and natively visualizes maps, lidar, and cameras. The driver simply opens the Foxglove app, draws a path, and executes the Autopilot script.

## 2. Infrastructure: Do we need a server? 
**No. For the MVP, an AWS server introduces an unnecessary point of failure.** Cellular (4G/5G) coverage in fields is incredibly unpredictable. A dropped connection during an investor pitch destroys credibility.

*   **The Bulletproof Setup (Local LAN):** We will deploy a standard, dedicated offline Wi-Fi Router placed on a table near the field. Both the Tractor and the Driver's Tablet will connect to this closed local Wi-Fi network. 
*   **Zero Latency:** The tablet communicates directly with the tractor's IP address (e.g., `192.168.1.50`). Commands are executed instantly (sub 5ms ping).
*   **Zero Risk:** Even if AWS crashes globally or you are in a literal dead-zone, the demo will execute flawlessly.
*   **Data Logging:** All heavy telemetry (rosbags) is continuously saved directly to the tractor's internal hard drive. No cloud syncing is attempted during the live demo to ensure zero network bottlenecks.

## 3. Disaster Recovery (The Investor Contingency)
Instead of relying on cloud backups to recover from hardware damage during the presentation, we optimize for speed.

*   **Pre-Cloned Hardware:** If the physical drive on the tractor fails or the OS corrupts right before the demo, downloading an update over 4G takes too long. We will carry a **pre-cloned, identical solid-state drive (SSD) or SD Card**. If disaster strikes, a technician swaps the physical drive in 60 seconds, and the tractor is instantly restored to its perfect functional state.
*   **Software Updates:** Updates to the algorithm are compiled locally on the developers' laptops. They are simply copied to the tractor over the local Wi-Fi prior to the demo. 

---

### Path from Today to the Physical MVP
1. **Week 1:** Complete localized simulation testing in Foxglove (verifying the Boustrophedon path math).
2. **Week 2:** Transition code to the physical hardware module; verify local hardware turning and speed controls.
3. **Week 3:** Setup the offline Wi-Fi Router; ensure the tablet successfully triggers the Autopilot locally using Foxglove.
4. **Week 4:** Final field rehearsals, aggressive bug fixing, and the Investor Demo.

---

## Appendix: Engineering Checklist - Hardware Size Calibration

As highlighted during our technical meetings, the math for the sensor fusion (EKF algorithm) does not need to be rewritten. However, the system's **Odometry Controller** must be updated with the precise physical dimensions of our custom tractor. If these are incorrect, the tractor will believe it rotated 90 degrees when it actually rotated 20, causing the navigational filter to crash.

**Action Item:** Once the physical chassis is built, use a tape measure and update the following exact files in our repository:

### 1. `config/controllers.yaml`
This file configures the ROS 2 software controller (`diff_drive_base_controller`). You must update:
*   **`wheel_separation`** (Distance between the centers of the left and right wheels in meters). Current default is `0.32`.
*   **`wheel_radius`** (Radius of the driving wheels in meters). Current default is `0.083`.

### 2. `arduino_bridge.py`
This is our custom Python bridge that translates ROS commands into electrical signals for the Arduino/Motors. Currently, the sizes are hardcoded at line 28. You must update:
*   **`self.wheel_base`** (Same as wheel separation). Current default is `0.40`.
*   **`self.wheel_radius`** (Same as wheel radius). Current default is `0.15`.

### 3. `config/hardware/yardforce500.yaml` (Critical for Transformation & Physics)
Your teammate has perfectly identified the third crucial file! This file configures the **URDF (Unified Robot Description Format)** which tells ROS exactly how big the tractor is physically, so it doesn't crash into walls, and knows exactly where the GPS antenna is located relative to the wheels. You must update:
*   **`chassis:`** Update `width`, `length`, and `mass` to match the physical steel frame.
*   **`wheel:`** Update `radius` and `offset` (where the wheels are attached relative to the center of the tractor).
*   **`gps: antenna: offset`** Extremely important! Measure exactly where the GPS puck is placed relative to the center of the wheels, otherwise your map will be distorted.

### 4. Custom MQTT Bridges (If testing remote commands)
Depending on which kinematics model you run in the field, check your Python bridge files:
*   `cloud_ackermann_mqtt.py` and `ackermann_hils_bridge.py`: If you switch the tractor to car-like Ackermann steering, you must update `self.wheelbase_L` (the distance from the front axle to the rear axle). Current default is `0.50`.

**Do NOT change the EKF covariances (`robot_localization.yaml`)**. Once you update the physical parameters in the files above, the odometer and URDF physics engine will begin providing accurate geometric data, and the 60-year-old EKF math will filter out the sensor noise perfectly.
