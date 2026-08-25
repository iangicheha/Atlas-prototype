# Atlas Architecture Overview

Project Atlas is a ROS 2 autonomy workspace for warehouse mobile robotics. The current implementation uses a generic simulated mobile robot as the integration platform; the same interfaces are intended to support the future TITAN and COLOSSUS target platforms.

## Layered autonomy architecture

```text
Sensors
   ↓
Perception
   ↓
Localization
   ↓
World Representation
   ↓
Global Planning
   ↓
Local Planning
   ↓
Motion Control
   ↓
Robot
```

The architecture keeps sensor drivers and simulation bridges separate from planning and control. This allows a simulated sensor or actuator to be replaced by a physical interface without requiring a wholesale rewrite of the autonomy stack.

## ROS 2 package graph

| Function | Package | Main interfaces |
|---|---|---|
| Bringup | `atlas_bringup` | Top-level launch orchestration |
| Robot description | `atlas_description` | URDF/Xacro, TF frames, sensor mounts |
| Meshes | `atlas_meshes` | Robot geometry and Gazebo resources |
| Simulation | `atlas_gazebo`, `atlas_isaac` | Gazebo Harmonic worlds, models, bridges, and future simulator integration |
| Control | `atlas_control` | `ros2_control`, differential drive, and velocity smoothing |
| Teleoperation | `atlas_teleop` | Manual velocity input and emergency stop |
| Perception | `atlas_lidar_processing`, `atlas_camera_processing` | LiDAR, camera, depth, stereo, and point-cloud interfaces |
| Localization | `atlas_localization` | EKF, IMU filtering, AMCL, and pose estimation |
| Mapping | `atlas_mapping` | SLAM Toolbox and map server |
| Navigation | `atlas_navigation` | Nav2 planners, controllers, costmaps, behaviors, and goals |
| Utilities | `atlas_utils` | Shared utilities and diagnostics |

## Sensor data flow

Gazebo publishes simulated sensor data through the ROS-Gazebo bridge. Perception packages consume the sensor topics and provide representations for navigation and state estimation.

```text
Gazebo sensors
  ├── 2-D LiDAR ───────────────→ scan / obstacle observations
  ├── IMU ──────────────────────→ orientation and acceleration
  ├── depth / stereo cameras ───→ images and depth point clouds
  ├── GPS ──────────────────────→ global position (when enabled)
  └── optional 3-D LiDAR ──────→ volumetric perception inputs
```

All of these interfaces are currently documented as **simulated**. Physical sensor integration is planned and must be validated separately.

## TF and state estimation

The intended TF chain is:

```text
map → odom → base_footprint → base_link → sensor frames
```

`atlas_localization` uses `robot_localization` and the IMU pipeline for the local odometric estimate. When a saved map is used, AMCL provides global localization and the `map → odom` transform. During mapping, SLAM Toolbox owns that transform instead. Mapping and AMCL must not be enabled together because both would publish `map → odom`.

## Mapping and navigation

SLAM Toolbox consumes LiDAR and odometry to build an occupancy map. Once a map is available, the map server and AMCL provide the global frame required by Nav2. `atlas_navigation` contains the Nav2 configuration, costmaps, planner and controller settings, behavior trees, and launch interface for goal execution.

The navigation flow is:

```text
Sensor observations → costmaps → global planner → local controller → `/cmd_vel`
                                                        ↓
                                           ros2_control / Gazebo
```

The configuration retains support for Nav2 MPPI, SMAC Hybrid-A*, recovery behaviors, replanning, and autonomous goal execution. These capabilities remain subject to validation on a host with the required ROS 2 and Gazebo dependencies.

## Control and simulation bridge

`atlas_control` describes the controller interfaces used by the simulated differential-drive robot. `atlas_gazebo` owns the world files, robot spawning, model resources, and ROS-Gazebo bridge configuration. The container workflow mounts the workspace at `/ros2_ws`; this path is intentionally retained because launch files and map workflows use it.

## TITAN and COLOSSUS extensibility

TITAN and COLOSSUS are target platform architectures, not current physical hardware claims. Their future descriptions can share the same autonomy package interfaces while differing in payload geometry, wheelbase, actuator limits, sensor mounting, and operating parameters. The current generic simulation provides the foundation for testing those interface boundaries before hardware-in-the-loop work begins.
