#!/bin/bash
# docker/entrypoint.sh — Container entrypoint: sources ROS 2 and workspace overlay.
set -e

. /opt/ros/jazzy/setup.bash

# Source the workspace overlay if it has been built
if [ -f /ros2_ws/install/setup.bash ]; then
    . /ros2_ws/install/setup.bash
fi

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Ensure Gazebo can find the gz_ros2_control system plugin (.so) installed by ROS 2
export GZ_SIM_SYSTEM_PLUGIN_PATH=/opt/ros/jazzy/lib:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}

# Sync any mesh files present in the bind-mounted src but missing from install.
# This handles STL files generated after the image was built (e.g. wheel_cap.stl).
MESH_SRC=/ros2_ws/src/rlai-bot/src/robot/rlai_meshes/meshes
MESH_DST=/ros2_ws/install/rlai_meshes/share/rlai_meshes/meshes
if [ -d "$MESH_SRC" ] && [ -d "$MESH_DST" ]; then
    for stl in "$MESH_SRC"/*.stl; do
        name=$(basename "$stl")
        if [ ! -e "$MESH_DST/$name" ]; then
            ln -sf "$stl" "$MESH_DST/$name"
        fi
    done
fi

# Sync any URDF/xacro files present in the bind-mounted src but missing from install.
# This handles new .urdf.xacro files added after the image was built.
URDF_SRC=/ros2_ws/src/rlai-bot/src/robot/rlai_description/urdf
URDF_DST=/ros2_ws/install/rlai_description/share/rlai_description/urdf
if [ -d "$URDF_SRC" ] && [ -d "$URDF_DST" ]; then
    while IFS= read -r -d '' f; do
        rel="${f#"$URDF_SRC"/}"
        dst="$URDF_DST/$rel"
        if [ ! -e "$dst" ]; then
            mkdir -p "$(dirname "$dst")"
            ln -sf "$f" "$dst"
        fi
    done < <(find "$URDF_SRC" \( -name "*.xacro" -o -name "*.urdf" \) -print0)
fi

exec "$@"
