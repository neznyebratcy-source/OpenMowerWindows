# Investor UX & Presentation Strategy
**Transforming Foxglove into a Professional Interface**

Foxglove out-of-the-box looks like a confusing dashboard for engineers. To secure investor confidence, we need it to look like a polished, consumer-ready application. 

Since our hardware timeline is aggressive, we will deploy **two completely different presentation strategies**, depending on the phase of the pitch.

---

## Part 1: The "Video Game" Simulation Demo (Next Week)
**Goal:** Prove to investors that our *software* algorithms (Coverage Path Planning, obstacle avoidance logic) are brilliant, even before the hardware is fully assembled. 

Since this takes place entirely in the "Matrix" (Gazebo 3D Simulation), we have absolute control over the visuals.

1.  **Virtual Woodlands & Obstacles:** We will inject `visualization_msgs` into Foxglove to spawn beautiful 3D Tree meshes and simulated fences. This makes the empty grid look like a real park.
2.  **Algorithm Visualization:** As the tractor drives, it will paint a glowing Green line showing its intended Boustrophedon path, and leave a solid Blue "mowed grass" trail behind it.
3.  **Simulated Lidar (Radar):** We will enable the 2D laser scanner in Gazebo. When the tractor approaches a fake tree, the investors will see the simulated radar bouncing off the tree, and the tractor intelligently steering around it. 

*This stage proves our AI works. It is visually stunning, but we must explicitly state that it is a digital twin simulation.*

---

## Part 2: The "Honest Hardware" MVP Demo (End of April)
**Goal:** Show the physical tractor driving itself in a real field. 

For the physical MVP, we strip away the magic. Since we may not have a functioning Lidar/Radar integrated by April, we cannot simulate fake trees—that would mislead the investors into thinking the tractor "saw" a tree when it was actually just driving blind along GPS coordinates.

For this physical stage, the Foxglove interface must be exceptionally clean and brutally honest:

1.  **The "Pretty" Dashboard Layout:** We will lock down Foxglove into a fixed 3-panel iPad layout:
    *   **Main Panel:** A 2D top-down map. No 3D virtual objects.
    *   **Camera Feed:** A live, real-time video stream from the tractor's physical camera. This proves it's not a simulation.
    *   **Command Bar:** Giant, intuitive `START` and `EMERGENCY STOP` buttons for the operator.
2.  **Satellite Map Integration:** Instead of a grey grid, we will configure Foxglove to use a Mapbox Satellite underlay. The investors will see the digital symbol of the tractor moving precisely over a Google-Earth photograph of the exact grass field they are standing next to.
3.  **Pure GPS Tracking:** We draw the intended geometrical route on the tablet. As the physical tractor drives, investors watch its pure RTK-GPS dot trace the exact path on the screen perfectly, proving our motor controllers and tracking are flawless—even without obstacle detection.

**Summary:** We use a visually spectacular simulation next week to sell the *Software Vision*, and a stripped-down, highly reliable Satellite Dashbaord in April to prove our *Hardware Execution*.
