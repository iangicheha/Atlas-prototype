# rlai_gazebo/models/

Custom Gazebo Fuel model assets for the rbot simulation.

## Adding Custom Models

Place Fuel-compatible model directories here. Each directory must contain:
- `model.config` — metadata (name, version, author, description)
- `model.sdf` — SDF geometry and plugins

`gazebo.launch.py` sets `GZ_SIM_RESOURCE_PATH` to include this
directory automatically, so models placed here are available to all worlds by name.

## Downloading from Gazebo Fuel

```bash
gz fuel download -u 'https://fuel.gazebosim.org/1.0/<org>/models/<name>'
# Example:
gz fuel download -u 'https://fuel.gazebosim.org/1.0/OpenRobotics/models/Shelf'
```

## Status

Phase 3 worlds (`empty.sdf`, `small_warehouse.sdf`) use primitive SDF geometry
(boxes/cylinders) only — no external mesh assets required.

Higher-fidelity mesh assets (shelves, pallets, forklifts) are candidates for later phases.
