# rlai_gazebo/models

Reusable Gazebo Harmonic model assets for rbot simulation worlds.

Each model directory is Fuel-compatible and contains:

- `model.config` — model metadata
- `model.sdf` — model geometry, visuals, and collision
- `meshes/` — optional local mesh files
- `materials/` — optional local material scripts/textures

Bundled models are intentionally low-poly and use simple collision geometry so Nav2, SLAM, and sensor demos stay responsive.

## Bundled warehouse assets

- `warehouse_shelf` — reusable shelf block for warehouse aisles
- `warehouse_pallet` — low-profile pallet obstacle
- `warehouse_pallet_jack` — static pallet jack visual obstacle
- `warehouse_box_cluster` — clutter group for local-planner stress tests
- `warehouse_trash_bin` — cylindrical obstacle for warehouse/office layouts
- `warehouse_floor_marking` — visual-only yellow aisle strip
- `charging_dock` — visual docking/charging target

## Adding models

Use stable lowercase names with underscores. Add the directory under this folder and reference it from worlds with:

```xml
<include>
  <uri>model://warehouse_shelf</uri>
  <pose>0 0 0 0 0 0</pose>
</include>
```

Keep collision shapes simpler than visuals. Avoid high-poly mesh collisions unless a model genuinely requires them.
