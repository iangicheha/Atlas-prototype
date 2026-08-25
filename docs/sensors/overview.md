# Atlas Sensor Overview

Project Atlas uses simulated sensors to provide the observations required by localization, mapping, perception, and navigation. The current repository should be understood as a simulation and autonomy foundation; the presence of a simulated sensor does not imply physical hardware integration.

| Sensor | Current simulation role | Autonomy contribution | Physical status |
|---|---|---|---|
| 2-D LiDAR | Publishes planar range observations | Obstacle detection, AMCL, costmaps, and SLAM Toolbox | Physical integration planned |
| IMU | Publishes orientation and inertial measurements | State estimation, odometry fusion, and motion stability | Physical integration planned |
| Depth camera | Publishes depth imagery and derived point clouds when enabled | Local obstacle geometry and perception inputs | Physical integration planned |
| Stereo camera | Provides stereo imagery through the camera processing pathway | Depth reconstruction and future learned perception | Physical integration planned |
| GPS | Provides simulated global position when enabled | Optional global state-estimation input | Physical integration planned |
| 3-D LiDAR | Optional simulated volumetric range source | Future 3-D obstacle and scene understanding | Physical integration planned |

## Data flow

```text
Simulated sensor → ROS 2 topic → perception / localization → world model → planner
```

Sensor topics, frames, and launch toggles are defined by the robot description, Gazebo bridge, perception, and localization packages. Before using a sensor in a new autonomy experiment, verify the topic name, frame ID, update rate, and timestamp behavior in the active simulation configuration.

## Validation boundary

Sensor publication and frame connectivity should be tested in a ROS 2 and Gazebo environment. If those dependencies are unavailable, the check must be recorded as **not tested** rather than inferred from configuration files. Physical sensor calibration, environmental robustness, and hardware timing remain outside the current repository implementation.
