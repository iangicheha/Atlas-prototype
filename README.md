<p align="center">
  <img src="docs/assets/rbot-logo.png" alt="rbot autonomous mobile robot logo" width="360">
</p>

<h1 align="center">rbot</h1>

<p align="center">
  An open-source Autonomous Mobile Robot simulation stack for ROS 2 Jazzy and Gazebo Harmonic.
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: Apache 2.0" src="https://img.shields.io/badge/License-Apache%202.0-blue.svg"></a>
  <img alt="ROS 2 Jazzy" src="https://img.shields.io/badge/ROS%202-Jazzy-22314E.svg">
  <img alt="Gazebo Harmonic" src="https://img.shields.io/badge/Gazebo-Harmonic-F58113.svg">
  <img alt="Ubuntu 24.04" src="https://img.shields.io/badge/Ubuntu-24.04-E95420.svg">
</p>

---

<p align="center">
  <a href="https://youtu.be/B-d64c-2Mw0">
    <img src="https://img.youtube.com/vi/B-d64c-2Mw0/maxresdefault.jpg" alt="Watch the rbot open-source ROS 2 AMR simulation demo" width="720">
  </a>
</p>

<p align="center">
  <a href="https://youtu.be/B-d64c-2Mw0">Watch the demo video</a>
</p>

---

## Overview

`rbot` is a simulation-first Autonomous Mobile Robot (AMR) reference stack for ROS 2 Jazzy and Gazebo Harmonic. It combines robot description, Gazebo simulation, `ros2_control`, teleoperation, sensor simulation, localization, mapping, and Nav2 navigation in one ROS 2 workspace.

The project is for ROS users, students, and robotics teams that need a practical AMR baseline to run, inspect, and adapt. Its value is in the integration: a current ROS 2 workspace, Docker-first workflows, modern Nav2 configuration, and documentation that follows the full mapping-to-navigation path.

Gazebo Harmonic is the supported simulator. Isaac Sim packages are present as scaffolding for planned future integration.

---

## What This Project Contributes

`rbot` packages the AMR simulation path into one workspace: a Gazebo Harmonic robot model, ROS-Gazebo bridges, `ros2_control`, teleoperation, sensor topics, EKF localization, SLAM Toolbox mapping, AMCL, and Nav2. 

| Area | Current support |
| --- | --- |
| Simulation | Gazebo Harmonic demo and benchmark worlds, URDF/Xacro robot description, generated meshes, and configurable launch arguments. |
| Control and teleoperation | `ros2_control`, differential-drive controller, joystick/keyboard teleop, and a convenience software stop service. |
| Sensors and perception hooks | 2-D LiDAR, IMU, depth camera, stereo camera, GPS, and optional 3-D LiDAR bridge paths. |
| Mapping and localization | SLAM Toolbox, AMCL, EKF, saved-map workflow, and example maps. |
| Navigation | Nav2 launch files, MPPI controller, SMAC Hybrid-A* planner, behavior trees, and a simple action client. |
| Developer workflow | Docker, Docker Compose, VS Code Dev Container, native Ubuntu 24.04 setup, CI, and tests. |
| Isaac Sim | Package scaffolding for future integration. Gazebo is the supported simulator today. |

---

## Mapping and Navigation Quick Path

Use these commands for a mapping and autonomous navigation loop.

Prerequisites: Docker with Compose support. For RViz on Linux, make sure X11 forwarding is available.

1. Start mapping with RViz:

   ```bash
   bash scripts/run_sim.sh --headless --rviz-mapping
   ```

   - Drive the robot through the map with teleop (next command).
   - See [Run mapping with SLAM Toolbox](#run-mapping-with-slam-toolbox) for how to save the map.

2. Start teleop:

   ```bash
   docker compose -f docker/docker-compose.yml run --rm teleop
   ```

   - Use the joystick or keyboard controls to cover open aisles, corners, and doorways.

3. Start navigation with RViz:

   ```bash
   bash scripts/run_sim.sh --headless --rviz-nav --map /ros2_ws/maps/my_map.yaml
   ```

   - In RViz2, use **Set Initial Pose** from the top panel to align AMCL with the robot.
   - Use **Nav2 Goal** from the top panel to send the robot to a target pose.

---

## Stack

| Layer | Technology |
| --- | --- |
| OS target | Ubuntu 24.04 LTS |
| ROS distribution | ROS 2 Jazzy Jalisco |
| Primary simulator | Gazebo Harmonic |
| Middleware | CycloneDDS |
| Robot model | URDF/Xacro + generated mesh assets |
| Control | `ros2_control`, `diff_drive_controller`, `joint_state_broadcaster` |
| Teleoperation | `joy_linux`, `teleop_twist_joy`, convenience software stop |
| Perception | 2-D LiDAR, optional 3-D point-cloud filtering, stereo/depth processing |
| Localization | `robot_localization` EKF, AMCL |
| Mapping | SLAM Toolbox online async and lifelong configs |
| Navigation | Nav2 with MPPI controller and SMAC Hybrid-A* planner |
| Containers | Docker, Docker Compose, VS Code Dev Container |

---

## Repository Layout

```text
rbot/
├── .devcontainer/        # VS Code Dev Container setup
├── .github/workflows/    # CI build, lint, and test workflow
├── docker/               # Dockerfiles, compose services, entrypoint
├── docs/                 # Architecture notes, sensor docs, tutorials
├── maps/                 # Example occupancy maps and metadata
├── scripts/              # Build, dependency, simulation, and mesh helpers
└── src/
    ├── bringup/          # Top-level simulation launch orchestration
    ├── control/          # ros2_control and teleoperation packages
    ├── localization/     # EKF and AMCL launch/config packages
    ├── mapping/          # SLAM Toolbox launch/config packages
    ├── navigation/       # Nav2 launch, params, behavior trees, client
    ├── perception/       # LiDAR and camera processing packages
    ├── robot/            # Robot description and mesh packages
    ├── simulation/       # Gazebo packages and Isaac scaffolding
    └── utils/            # Shared utility package placeholder
```

---

## Quick Start: Docker

Docker is the recommended path for first-time users because it keeps ROS, Gazebo, and system dependencies isolated.

### 1. Install host requirements

Install Docker with Compose support. For GUI simulation on Linux, make sure X11 forwarding is available.

### 2. Build and run the Gazebo stack

```bash
bash scripts/run_sim.sh
```

Useful variants:

```bash
bash scripts/run_sim.sh --headless
bash scripts/run_sim.sh --rviz
bash scripts/run_sim.sh --rviz-nav
bash scripts/run_sim.sh --headless --rviz-nav --map /ros2_ws/maps/my_map.yaml
bash scripts/run_sim.sh --headless --rviz-mapping
bash scripts/run_sim.sh --headless world:=large_warehouse gps_enabled:=true
```

The script starts services from `docker/docker-compose.yml` and launches the simulation stack inside the container. Use `--map` with `--rviz-nav` when AMCL/Nav2 should localize against a specific map YAML mounted under `/ros2_ws/maps/`.

Extra arguments after the script flags are forwarded to the simulation launch service. Pass them as standard whitespace-free ROS launch tokens such as `name:=value`.

Bundled Gazebo worlds include the default warehouse plus richer demo and benchmark scenarios:

```bash
bash scripts/run_sim.sh world:=demo_warehouse_visual
bash scripts/run_sim.sh world:=benchmark_warehouse_easy
bash scripts/run_sim.sh world:=benchmark_warehouse_medium
bash scripts/run_sim.sh world:=benchmark_warehouse_hard
```

Use the same `world:=...` argument with `--rviz-mapping` to build maps in each scenario.

### 3. Alternative Docker helper

```bash
zsh scripts/sim_docker.sh
zsh scripts/sim_docker.sh --headless
zsh scripts/sim_docker.sh --shell
zsh scripts/sim_docker.sh world:=large_warehouse
```

Use this helper when you want direct `docker run` style control or an interactive shell in the simulation image.

---

## Quick Start: Native Ubuntu 24.04

Native setup is useful when you already work in a ROS 2 Jazzy environment.

```bash
bash scripts/install_deps.sh
bash scripts/build.sh
source install/setup.bash
ros2 launch rlai_bringup simulation.launch.py
```

To launch a specific world:

```bash
ros2 launch rlai_bringup simulation.launch.py world:=small_warehouse
```

Headless Gazebo:

```bash
ros2 launch rlai_bringup simulation.launch.py headless:=true
```

---

## Common Workflows

### Launch simulation with default localization

```bash
ros2 launch rlai_bringup simulation.launch.py localization_enabled:=true
```

This starts Gazebo, robot description publishing, ros2_control, and EKF localization.

### Enable joystick teleoperation

```bash
ros2 launch rlai_bringup simulation.launch.py teleop_enabled:=true
```

The joystick configuration lives in:

```text
src/control/rlai_teleop/config/joystick.yaml
```

The convenience software stop service is available at:

```bash
ros2 service call /e_stop std_srvs/srv/Trigger {}
```

This service publishes zero velocity commands while engaged.

### Run mapping with SLAM Toolbox

```bash
ros2 launch rlai_bringup simulation.launch.py \
  mapping_enabled:=true \
  slam_rviz_enabled:=true
```

Save the map from the mapping container when coverage looks good. When launched through the quick path, the mapping container is named `rlai_sim_mapping`:

```bash
docker exec -it rlai_sim_mapping ros2 run nav2_map_server map_saver_cli -f /ros2_ws/maps/my_map
```

Do not enable `mapping_enabled:=true` and `use_amcl:=true` at the same time. Both publish `map -> odom`.

### Run AMCL with a saved map

```bash
ros2 launch rlai_bringup simulation.launch.py \
  use_amcl:=true \
  map_yaml_file:=/absolute/path/to/map.yaml
```

Example maps are stored in `maps/`.

### Launch Nav2 directly

```bash
ros2 launch rlai_navigation navigation.launch.py \
  map:=/absolute/path/to/map.yaml
```

Use this when localization is already running and you want to focus on Nav2 behavior.

### Send a navigation goal programmatically

```bash
ros2 run rlai_navigation nav_client --ros-args \
  -p x:=3.0 \
  -p y:=2.0 \
  -p yaw:=0.0
```

Patrol mode:

```bash
ros2 run rlai_navigation nav_client --ros-args -p mode:=patrol
```

---

## Package Index

| Package | Type | Purpose |
| --- | --- | --- |
| `rlai_description` | `ament_cmake` | Robot URDF/Xacro, sensor mounts, payload platform, RViz configs |
| `rlai_meshes` | `ament_cmake` | Mesh assets used by the robot description |
| `rlai_gazebo` | `ament_cmake` | Gazebo worlds, launch files, ROS-Gazebo bridge config |
| `rlai_isaac` | `ament_python` | Scaffold package for planned Isaac Sim integration |
| `rlai_control` | `ament_cmake` | `ros2_control` controller configuration and launch |
| `rlai_teleop` | `ament_python` | Joystick teleoperation and convenience software stop node |
| `rlai_lidar_processing` | `ament_cmake` | Optional 3-D point-cloud height filtering and voxel downsampling |
| `rlai_camera_processing` | `ament_cmake` | Stereo disparity and depth point-cloud processing launch/config |
| `rlai_localization` | `ament_python` | IMU filtering, EKF, and AMCL launch/config |
| `rlai_mapping` | `ament_python` | SLAM Toolbox mapping and map-server launch/config |
| `rlai_navigation` | `ament_python` | Nav2 parameters, behavior trees, launch, and action client |
| `rlai_bringup` | `ament_python` | Top-level simulation bringup and stack orchestration |
| `rlai_utils` | `ament_python` | Shared utility package scaffold |

---

## Architecture Notes

### TF ownership

The stack uses a standard mobile robot TF chain:

```text
map -> odom -> base_footprint -> base_link -> sensor frames
```

Ownership is intentionally split:

- EKF publishes `odom -> base_footprint`.
- AMCL or SLAM Toolbox publishes `map -> odom`.
- Robot State Publisher publishes `base_footprint -> base_link` and sensor frames.

Avoid enabling multiple nodes that publish the same transform.

### Command velocity path

```text
teleop / Nav2 -> /cmd_vel -> velocity_smoother -> /diff_drive_controller/cmd_vel
```

The stack uses `TwistStamped` commands because the Jazzy `diff_drive_controller` expects stamped velocity input. The software stop node also publishes to `/cmd_vel`; it is a convenience mechanism for simulation and development.

### Simulation bridge

Gazebo topics are bridged through:

```text
src/simulation/rlai_gazebo/config/ros_gz_bridge.yaml
```

`/joint_states` is intentionally not bridged because `joint_state_broadcaster` owns that ROS topic.

---

## References and Prior Art

`rbot` builds on established ROS 2 projects and examples:

- [ROS 2 Jazzy documentation](https://docs.ros.org/en/jazzy/)
- [Gazebo Harmonic documentation](https://gazebosim.org/docs/harmonic/)
- [Nav2 documentation and tutorials](https://docs.nav2.org/)
- [SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox)
- [`robot_localization`](https://github.com/cra-ros-pkg/robot_localization)
- [`ros2_control`](https://control.ros.org/jazzy/index.html)
- [BCR Bot](https://github.com/blackcoffeerobotics/bcr_bot)
- [Linorobot2](https://github.com/linorobot/linorobot2)
- [ROSNav](https://github.com/ApolloAuto/rosnav)

---

## Development

### Build

```bash
bash scripts/build.sh
```

Or manually:

```bash
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
```

### Test

```bash
source install/setup.bash
colcon test --event-handlers console_cohesion+ --return-code-on-test-failure
colcon test-result --verbose
```

### Lint Python packages

```bash
flake8 src --max-line-length=100 --extend-ignore=E203 --exclude=__pycache__
```

### Validate launch-file syntax quickly

```bash
python3 -m compileall -q src scripts
```

---

## Troubleshooting

### Gazebo GUI does not open from Docker

Allow local Docker containers to connect to your X server:

```bash
xhost +local:docker
```

Then rerun the simulation script.

### ROS commands cannot find packages

Source the workspace after building:

```bash
source install/setup.bash
```

If using Docker, open a shell in the built container and source the installed workspace there.

### Nav2 or AMCL cannot configure

Check that a valid map file was provided when `use_amcl:=true`:

```bash
ros2 launch rlai_bringup simulation.launch.py \
  use_amcl:=true \
  map_yaml_file:=/absolute/path/to/map.yaml
```

### TF conflicts or unstable localization

Make sure only one component publishes each transform:

- EKF: `odom -> base_footprint`
- AMCL or SLAM Toolbox: `map -> odom`
- Robot State Publisher: robot links and sensor frames

Do not run AMCL and SLAM mapping together unless you intentionally change TF ownership.

### Docker build is slow

The Gazebo image installs ROS, Gazebo, Nav2, SLAM, perception, and control dependencies. The first build can take several minutes; later builds should reuse Docker layers.

---

## Roadmap

Future extension points:

- Isaac Sim integration
- Expanded benchmarks and automated scenario tests
- Additional warehouse, outdoor, and mixed-layout environments
- More perception and autonomy examples

---

## Contributing

Contributions are welcome. Start with [`CONTRIBUTING.md`](CONTRIBUTING.md) for development workflow, coding standards, and pull request guidance.

Good first contributions include:

- Improving setup instructions or troubleshooting notes.
- Adding reproducible simulation scenarios.
- Tuning navigation, localization, or mapping configs with before/after evidence.
- Adding tests or validation scripts for launch files, URDF/Xacro, and Gazebo worlds.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).

Copyright 2026 Robolabs AI (RLXAI ROBOLABSAI PRIVATE LIMITED).
