# 📝 Meeting Summary: Tractor Sensor Fusion & EKF
**Topic:** How the tractor knows exactly where it is on the field.

## 1. What is EKF?
EKF stands for **Extended Kalman Filter**, a foundational algorithm in robotics prototyping. Since no single sensor is perfect, the EKF uses probability to merge data from multiple noisy sensors into one highly accurate location estimate.

## 2. How our Tractor calculates position
We have three primary sensors telling us where the tractor is:
1.  **IMU (Inertial Measurement Unit):** Measures acceleration over time. By integrating acceleration, we get the distance traveled.
2.  **Odometer (Wheel Encoders):** Measures wheel rotations to calculate distance traveled.
3.  **GPS (RTK):** Gives us absolute global coordinates.

**The Problem:** The IMU and Odometer will often disagree slightly due to wheel slip or sensor noise.
**The Solution (The Filter):** The EKF doesn't just guess; it calculates the probability of error. For example, it might determine there is a 30% chance we moved 1 meter, and a 5% chance we moved 0.5 meters. By multiplying these probability curves across all sensors, it finds the single most accurate physical coordinate.

## 3. Our "Dual Filter" Architecture
We are specifically using a dual-filter setup:
*   **Filter 1 (Local):** Merges IMU and Odometry for smooth, continuous short-term tracking.
*   **Filter 2 (Global):** Takes the output of Filter 1 and merges it with the GPS data to keep the tractor perfectly aligned with the real world over long distances.

## 4. Key Decisions & Deadlines (End of April)
*   **Don't Touch the Core Code:** The EKF is a 60-year-old math concept and is **already fully programmed** in the current open-source repository we are using (`robot_localization`). While there are newer, flashier AI methods available today, we do not need them for the April MVP. **We do not need to rewrite this; we just need to understand it and run it.**
*   **Hardware:** This entire filtering process is lightweight and will run locally on the robot's onboard computer (Raspberry Pi/Jetson). It will absolutely be able to handle the load.

## 5. Next Steps / Action Items for Us
1.  **Configuration Check:** We need to dive into the codebase (specifically looking for YAML config files) to find exactly where to input our physical hardware parameters. When we change the size of the tractor or the diameter of the wheels, we need to know exactly which configuration variables to update.
2.  **Open Question for Research:** Does ROS 2 have an automated way to tune the EKF covariance matrices (the error coefficients), or will we have to manually tune these numbers during our initial field tests?
