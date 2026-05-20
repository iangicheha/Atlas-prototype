# Adding Gazebo Models

rbot stores official Gazebo models in:

```text
src/simulation/rlai_gazebo/models
```

Each model must use this layout:

```text
model_name/
  model.config
  model.sdf
  meshes/      # optional
  materials/   # optional
```

Use lowercase names with underscores, for example:

```text
warehouse_shelf
charging_dock
```

Reference bundled models from worlds with:

```xml
<include>
  <uri>model://warehouse_shelf</uri>
  <pose>0 0 0 0 0 0</pose>
</include>
```

## Collision guidance

Keep collision geometry simple. A detailed visual mesh is fine, but the collision should usually be a box, cylinder, sphere, or small set of primitives.

Good:

```xml
<collision name="collision">
  <geometry><box><size>1.2 0.8 0.4</size></box></geometry>
</collision>
```

Avoid high-poly mesh collisions for common objects because they slow down simulation and can make navigation tests brittle.

## Validation

Run:

```bash
pytest tests/test_gazebo_assets.py -q
```

The test checks that bundled model directories have `model.config`, `model.sdf`, matching model names, and static models.
