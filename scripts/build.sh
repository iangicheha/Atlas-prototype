#!/bin/bash
# scripts/build.sh
# Builds the rbot ROS 2 workspace using colcon.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(dirname "$SCRIPT_DIR")"

# Source ROS 2 if not already sourced
if [ -z "$ROS_DISTRO" ]; then
    . /opt/ros/jazzy/setup.bash
fi

cd "$WS_ROOT"

echo "==> Building workspace at $WS_ROOT"
colcon build \
    --symlink-install \
    --cmake-args -DCMAKE_BUILD_TYPE=Release \
    --event-handlers console_cohesion+

echo ""
echo "Build complete. Source the workspace with:"
echo "  source $WS_ROOT/install/setup.bash"
