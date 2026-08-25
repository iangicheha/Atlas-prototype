# PROJECT ATLAS

<p align="center">
  <img src="docs/assets/rbot-logo.png" alt="Project Atlas Autonomous Mobile Robot" width="360">
</p>

<h1 align="center">Project Atlas</h1>

<p align="center">
  <strong>Autonomous Mobile Robots for Warehouse Logistics</strong>
</p>

<p align="center">
  A ROS 2-based autonomous robotics platform for perception, localization,
  mapping, navigation, obstacle avoidance, and intelligent warehouse mobility.
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/badge/License-Apache%202.0-blue.svg"></a>
  <img alt="ROS 2 Jazzy" src="https://img.shields.io/badge/ROS%202-Jazzy-22314E.svg">
  <img alt="Gazebo Harmonic" src="https://img.shields.io/badge/Gazebo-Harmonic-F58113.svg">
  <img alt="Ubuntu 24.04" src="https://img.shields.io/badge/Ubuntu-24.04-E95420.svg">
  <img alt="Project Atlas" src="https://img.shields.io/badge/Project-Atlas-black.svg">
</p>

---

## Overview

**Project Atlas** is an autonomous mobile robot platform being developed by **Faraday's Lab** for warehouse logistics.

The system is designed around a simple objective:

> **Enable mobile robots to perceive warehouse environments, understand where they are, plan safe paths, and autonomously move material between locations.**

Atlas combines simulation, robot control, perception, localization, mapping, and autonomous navigation into a unified ROS 2 architecture.

The platform is being developed as a foundation for real-world warehouse automation rather than as a standalone simulation exercise.

The current development environment uses **ROS 2 Jazzy**, **Gazebo Harmonic**, **Nav2**, **SLAM Toolbox**, `ros2_control`, sensor simulation, and autonomous navigation components.

---

# The Atlas Platform

Project Atlas is designed around two autonomous mobile robot platforms serving different warehouse requirements.

| Platform     | Target Payload | Primary Role                                                             |
| ------------ | -------------: | ------------------------------------------------------------------------ |
| **TITAN**    |         ~60 kg | Small-load transport, picking support, intra-warehouse material movement |
| **COLOSSUS** |      ~1,000 kg | Pallet and heavy-load transportation                                     |

Both platforms are intended to share a common autonomy architecture while allowing their mechanical platforms, payload systems, and operational parameters to differ.

### Common autonomy capabilities

* Autonomous navigation
* Obstacle detection
* Dynamic obstacle avoidance
* Mapping
* Localization
* Path planning
* Sensor fusion
* Warehouse environment understanding
* Waypoint navigation
* Autonomous goal execution
* Simulation-based testing
* Future multi-robot coordination

---

# Why Atlas?

Traditional warehouse automation often requires extensive facility-specific integration.

Atlas is being developed around a different approach:

**Build a generalizable autonomy stack that can be adapted to different warehouse environments.**

Instead of designing the autonomy system around a single fixed environment, Atlas separates:

```text
Robot Hardware
      │
      ▼
Sensor Layer
      │
      ▼
Perception
      │
      ▼
Localization
      │
      ▼
World Representation
      │
      ▼
Path Planning
      │
      ▼
Motion Control
      │
      ▼
Robot
```

This architecture allows the same core autonomy software to evolve across different robot platforms and warehouse layouts.

---

# System Architecture

```text
                         PROJECT ATLAS
                              │
             ┌────────────────┴────────────────┐
             │                                 │
       Robot Platforms                   Autonomy Stack
             │                                 │
       ┌─────┴─────┐                 ┌─────────┴─────────┐
       │           │                 │                   │
     TITAN      COLOSSUS        Perception          Navigation
       │           │                 │                   │
       └─────┬─────┘                 ├── LiDAR           ├── Nav2
             │                       ├── Camera          ├── Planner
             │                       ├── IMU             ├── Controller
             │                       └── Sensor Fusion   └── Behaviors
             │
             └──────────────────────────┐
                                        │
                              Localization & Mapping
                                        │
                              ┌─────────┴─────────┐
                              │                   │
                           SLAM Toolbox          AMCL
                              │                   │
                              └─────────┬─────────┘
                                        │
                                     ROS 2
                                        │
                                Gazebo Harmonic
```

---

# Autonomous Navigation

Atlas uses the ROS 2 navigation ecosystem as the foundation for autonomous mobility.

The navigation pipeline is designed around:

```text
Sensors
   │
   ▼
Perception
   │
   ▼
Localization
   │
   ▼
Map / World Model
   │
   ▼
Global Planner
   │
   ▼
Local Controller
   │
   ▼
Velocity Commands
   │
   ▼
Robot
```

The system can:

1. Build a map of an environment.
2. Localize the robot within the map.
3. Receive a navigation goal.
4. Generate a feasible path.
5. Detect obstacles.
6. Re-plan when the environment changes.
7. Execute the trajectory.
8. Continuously correct its motion using sensor feedback.

---

# Perception

Atlas is designed to operate using multiple complementary sensors.

Current simulation pathways include:

* 2-D LiDAR
* Depth camera
* Stereo camera
* IMU
* GPS
* Optional 3-D LiDAR

The purpose of the perception layer is not simply to detect objects.

It provides the information required for the robot to answer:

> **What is around me, where is it, and how does it affect the path I should take?**

Future development will expand the perception layer toward learned perception and semantic understanding of warehouse environments.

---

# Mapping & Localization

Atlas supports both mapping and localization workflows.

### Mapping

SLAM Toolbox is used to construct occupancy maps while the robot explores an environment.

```text
LiDAR + Odometry + IMU
          │
          ▼
     SLAM Toolbox
          │
          ▼
      Occupancy Map
```

### Localization

Once a map exists, the robot can localize against it using AMCL and sensor fusion.

```text
Saved Map
   │
   ├── LiDAR
   ├── Odometry
   └── IMU
          │
          ▼
         AMCL
          │
          ▼
       Robot Pose
```

The standard TF structure is:

```text
map
 │
 ▼
odom
 │
 ▼
base_footprint
 │
 ▼
base_link
 │
 ├── lidar
 ├── imu
 ├── camera
 └── other sensors
```

---

# Obstacle Avoidance

A core capability of Atlas is the ability to navigate around obstacles rather than simply follow a pre-computed route.

The intended behavior is:

```text
             OBSTACLE
                ███
                ███
                ███

Robot ──────────►

        Global Path
──────────────────────────

             ↓ obstacle detected

Robot ────────╮
              │
              ╰──────────►
                    New Safe Path
```

The navigation system continuously processes sensor information and can modify the local trajectory when obstacles appear.

This provides the foundation for operation in dynamic warehouse environments where workers, forklifts, pallets, and other robots may change the environment.

---

# Simulation

Gazebo Harmonic is the primary simulation environment.

Simulation allows Atlas to test autonomy before deployment to physical hardware.

Current simulation capabilities include:

* Warehouse environments
* Robot models
* Sensor simulation
* Differential-drive control
* Mapping
* Localization
* Autonomous navigation
* Obstacle avoidance
* Navigation benchmarks
* RViz visualization

Example environments include:

```text
default warehouse
demo warehouse
large warehouse
benchmark warehouse - easy
benchmark warehouse - medium
benchmark warehouse - hard
```

---

# Technology Stack

| Layer               | Technology              |
| ------------------- | ----------------------- |
| Operating System    | Ubuntu 24.04 LTS        |
| Robotics Middleware | ROS 2 Jazzy             |
| Simulation          | Gazebo Harmonic         |
| Navigation          | Nav2                    |
| Mapping             | SLAM Toolbox            |
| Localization        | AMCL                    |
| Sensor Fusion       | robot_localization      |
| Robot Control       | ros2_control            |
| Robot Description   | URDF / Xacro            |
| Visualization       | RViz2                   |
| Middleware          | CycloneDDS              |
| Containers          | Docker / Docker Compose |
| Development         | VS Code Dev Container   |
| Languages           | C++, Python, XML, YAML  |

---

# Repository Structure

```text
Atlas-prototype/
│
├── .devcontainer/
│
├── .github/
│   └── workflows/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/
│   ├── assets/
│   ├── architecture/
│   └── tutorials/
│
├── maps/
│
├── scripts/
│   ├── build.sh
│   ├── install_deps.sh
│   └── run_sim.sh
│
└── src/
    │
    ├── bringup/
    │
    ├── control/
    │
    ├── localization/
    │
    ├── mapping/
    │
    ├── navigation/
    │
    ├── perception/
    │
    ├── robot/
    │
    ├── simulation/
    │
    └── utils/
```

---

# Quick Start

## Requirements

Recommended development environment:

* Ubuntu 24.04 LTS
* ROS 2 Jazzy
* Gazebo Harmonic
* Docker
* Docker Compose
* NVIDIA GPU support where available for future perception workloads

Docker is recommended for reproducible development.

---

## Run the Simulation

Clone the repository:

```bash
git clone https://github.com/iangicheha/Atlas-prototype.git
cd Atlas-prototype
```

Start the simulation:

```bash
bash scripts/run_sim.sh
```

Headless mode:

```bash
bash scripts/run_sim.sh --headless
```

Launch with RViz:

```bash
bash scripts/run_sim.sh --rviz
```

Launch navigation:

```bash
bash scripts/run_sim.sh --rviz-nav
```

Launch mapping:

```bash
bash scripts/run_sim.sh --headless --rviz-mapping
```

---

# Mapping Workflow

Start the mapping environment:

```bash
bash scripts/run_sim.sh --headless --rviz-mapping
```

Drive the robot through the environment using teleoperation.

Ensure the robot covers:

* Long aisles
* Corners
* Intersections
* Doorways
* Open areas
* Areas around shelving

Save the resulting map:

```bash
docker exec -it rlai_sim_mapping \
ros2 run nav2_map_server map_saver_cli \
-f /ros2_ws/maps/my_map
```

---

# Autonomous Navigation

Once a map has been created:

```bash
bash scripts/run_sim.sh \
  --headless \
  --rviz-nav \
  --map /ros2_ws/maps/my_map.yaml
```

In RViz2:

1. Set the robot's initial pose.
2. Select **Nav2 Goal**.
3. Click a target location.
4. Observe the planner generate a path.
5. Observe the robot execute the trajectory.

The navigation stack is responsible for planning and executing the movement.

---

# Teleoperation

Teleoperation can be used to manually inspect environments and create maps.

```bash
docker compose \
  -f docker/docker-compose.yml \
  run --rm teleop
```

A software emergency stop is also available:

```bash
ros2 service call /e_stop std_srvs/srv/Trigger {}
```

---

# Native ROS 2 Development

For a native Ubuntu environment:

```bash
bash scripts/install_deps.sh
bash scripts/build.sh
source install/setup.bash
```

Launch the simulation:

```bash
ros2 launch rlai_bringup simulation.launch.py
```

Launch a specific warehouse:

```bash
ros2 launch rlai_bringup simulation.launch.py \
  world:=large_warehouse
```

---

# Development

Build the workspace:

```bash
bash scripts/build.sh
```

Or:

```bash
source /opt/ros/jazzy/setup.bash

colcon build \
  --symlink-install \
  --cmake-args \
  -DCMAKE_BUILD_TYPE=Release
```

Run tests:

```bash
source install/setup.bash

colcon test \
  --event-handlers console_cohesion+ \
  --return-code-on-test-failure
```

Check results:

```bash
colcon test-result --verbose
```

---

# Development Roadmap

Project Atlas is being developed progressively toward physical warehouse deployment.

### Phase 1 — Simulation Foundation

* [x] ROS 2 architecture
* [x] Gazebo simulation
* [x] Robot description
* [x] Sensor simulation
* [x] `ros2_control`
* [x] Teleoperation
* [x] SLAM
* [x] Localization
* [x] Nav2 integration
* [x] Warehouse environments

### Phase 2 — Autonomous Mobility

* [x] Autonomous goal navigation
* [x] Global path planning
* [x] Local trajectory control
* [x] Dynamic obstacle handling
* [ ] Expanded warehouse benchmarks
* [ ] Automated navigation evaluation
* [ ] Recovery behavior evaluation
* [ ] Long-duration autonomy testing

### Phase 3 — Intelligent Perception

* [ ] Learned object detection
* [ ] Semantic perception
* [ ] Pallet detection
* [ ] Human detection
* [ ] Warehouse scene understanding
* [ ] Learned obstacle classification
* [ ] Perception-driven navigation

### Phase 4 — Physical Atlas

* [ ] TITAN prototype
* [ ] COLOSSUS prototype
* [ ] Embedded compute integration
* [ ] Real sensor integration
* [ ] Motor controller integration
* [ ] Hardware-in-the-loop testing
* [ ] Physical warehouse trials

### Phase 5 — Multi-Robot Warehouse Intelligence

* [ ] Multi-robot coordination
* [ ] Fleet management
* [ ] Task allocation
* [ ] Traffic management
* [ ] Collision-aware fleet planning
* [ ] Warehouse digital twin integration

---

# Research Direction

The long-term objective of Atlas is not simply to reproduce existing mobile robot navigation.

The project investigates how autonomous mobile robots can become more **generalizable, adaptable, and intelligent across different warehouse environments**.

The autonomy stack is therefore being developed around three increasingly important capabilities:

```text
                ATLAS AUTONOMY
                     │
        ┌────────────┼────────────┐
        │            │            │
     PERCEIVE     REASON        ACT
        │            │            │
        ▼            ▼            ▼
     Sensors      World Model   Motion
     Objects      Context       Navigation
     Obstacles    Goals         Manipulation
```

The ultimate direction is a system capable of understanding a warehouse as an operational environment rather than simply navigating a static map.

---

# Project Philosophy

Atlas follows several principles:

### 1. Simulation before deployment

Autonomy should be tested extensively in simulation before being transferred to physical hardware.

### 2. Hardware-independent autonomy

The core intelligence should not be tightly coupled to one mechanical platform.

### 3. Generalizable navigation

The system should be capable of adapting to different layouts rather than relying entirely on hand-tuned environments.

### 4. Perception-driven behavior

The robot should use what it perceives to continuously update its understanding of the environment.

### 5. Reproducible robotics

Simulation environments, configurations, and development workflows should be reproducible by other researchers and engineers.

---

# Team

**Faraday's Lab**

### Project Atlas

**Ian Gicheha**
**Joe Albert**
**Ray Wekesa**

Electrical & Mechatronics Engineering

---

# Acknowledgements

Atlas builds upon the open-source robotics ecosystem, including:

* ROS 2
* Gazebo
* Nav2
* SLAM Toolbox
* `robot_localization`
* `ros2_control`
* RViz2

The project is intended to contribute back to the robotics community through reproducible simulation, research, and autonomous robotics development.

---

# License

This project is licensed under the **Apache License 2.0**.

See [`LICENSE`](LICENSE) for the complete license text.

---

<p align="center">
  <strong>PROJECT ATLAS</strong><br>
  Autonomous Mobile Robotics for Warehouse Logistics
</p>

<p align="center">
  Built by <strong>Faraday's Lab</strong>
</p>
