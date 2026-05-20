# Testing rbot Sensors in Rich Gazebo Worlds

Use rich worlds to validate that perception, localization, mapping, and navigation still work when the scene contains shelves, pallets, clutter, and narrow aisles.

## Recommended smoke sequence

Start with the easy benchmark:

```bash
ros2 launch rlai_bringup simulation.launch.py \
  world:=benchmark_warehouse_easy \
  mapping_enabled:=true
```

Verify core topics:

```bash
ros2 topic list | grep -E '/clock|/scan|/tf|/odom|/cmd_vel'
```

Check laser data:

```bash
ros2 topic echo /scan --once
```

Check transforms:

```bash
ros2 run tf2_ros tf2_echo odom base_footprint
```

## Progression

1. `benchmark_warehouse_easy` — basic spawn, scan, TF, and mapping.
2. `benchmark_warehouse_medium` — local planner and costmap tuning.
3. `benchmark_warehouse_hard` — recovery behavior and tight-aisle navigation.
4. `demo_warehouse_visual` — final screenshot/video validation.

## What to watch

- Missing model errors in Gazebo output.
- Empty `/scan` data.
- TF gaps between `map`, `odom`, and `base_footprint`.
- Costmap inflation closing narrow aisles.
- Excessively slow simulation from detailed collision geometry.
