# Using Custom Gazebo Worlds

rbot ships bundled worlds in:

```text
src/simulation/rlai_gazebo/worlds
```

Run a bundled world by name:

```bash
ros2 launch rlai_bringup simulation.launch.py world:=benchmark_warehouse_easy
```

The launch file resolves this to:

```text
rlai_gazebo/worlds/benchmark_warehouse_easy.sdf
```

## Bundled scenario worlds

- `demo_warehouse_visual` — polished warehouse scene for demos and screenshots
- `benchmark_warehouse_easy` — simple navigation and mapping smoke test
- `benchmark_warehouse_medium` — tighter aisles and clutter
- `benchmark_warehouse_hard` — tight turns, clutter, and harder local planning

## Running an external world

Use an absolute path for the world and provide an extra model resource path when the world depends on external models:

```bash
ros2 launch rlai_bringup simulation.launch.py \
  world:=/absolute/path/to/external_world.sdf \
  extra_gz_resource_path:=/absolute/path/to/external_models
```

`extra_gz_resource_path` is appended to rbot's bundled Gazebo resource path, so local rbot models and external models can be used together.

## Docker wrapper

The wrapper forwards extra ROS launch arguments:

```bash
bash scripts/run_sim.sh --headless world:=benchmark_warehouse_medium
```

External paths must exist inside the container. For external host folders, either mount them into the container or run the ROS launch command in a development shell where the paths are available.
