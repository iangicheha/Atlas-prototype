#!/usr/bin/env zsh
# scripts/sim_docker.sh
# Build (if needed) and run the rbot Gazebo simulation inside Docker.
#
# Usage:
#   zsh scripts/sim_docker.sh              # build + run (small_warehouse)
#   zsh scripts/sim_docker.sh --build-only # build image only
#   zsh scripts/sim_docker.sh --shell      # interactive shell in container
#   zsh scripts/sim_docker.sh --headless   # headless Gazebo (no GUI window)
#   zsh scripts/sim_docker.sh world:=large_warehouse
#
# Options are forwarded to the launch file (e.g. world:=large_warehouse).

set -euo pipefail

SCRIPT_DIR="${0:A:h}"
REPO_ROOT="${SCRIPT_DIR:h}"
COMPOSE_FILE="${REPO_ROOT}/docker/docker-compose.yml"
IMAGE_NAME="rlai-bot:gazebo"

# ── Argument parsing ──────────────────────────────────────────────────────────
BUILD_ONLY=false
OPEN_SHELL=false
HEADLESS=false
LAUNCH_ARGS=()

for arg in "$@"; do
  case "$arg" in
    --build-only) BUILD_ONLY=true ;;
    --shell)      OPEN_SHELL=true ;;
    --headless)   HEADLESS=true ;;
    *)            LAUNCH_ARGS+=("$arg") ;;
  esac
done

# ── Build image if not present or --build-only requested ─────────────────────
if ! docker image inspect "$IMAGE_NAME" &>/dev/null || [[ "$BUILD_ONLY" == true ]]; then
  echo "==> Building Docker image $IMAGE_NAME (this may take 10-15 minutes) ..."
  docker compose -f "$COMPOSE_FILE" build sim
fi

[[ "$BUILD_ONLY" == true ]] && { echo "==> Build complete."; exit 0; }

# ── Allow X11 connections from Docker ────────────────────────────────────────
if [[ "$HEADLESS" == false ]]; then
  echo "==> Allowing X11 connections from local Docker containers ..."
  xhost +local:docker 2>/dev/null || true

  # Refresh xauth so GUI containers can connect to the host X server.
  touch /tmp/.docker.xauth
  xauth nlist "$DISPLAY" 2>/dev/null | sed 's/^..../ffff/' | \
    xauth -f /tmp/.docker.xauth nmerge - 2>/dev/null || true
fi

# ── Open interactive shell ────────────────────────────────────────────────────
if [[ "$OPEN_SHELL" == true ]]; then
  echo "==> Opening interactive shell in container ..."
  docker compose -f "$COMPOSE_FILE" run --rm shell
  exit 0
fi

# ── Build the docker run command ──────────────────────────────────────────────
WORLD="small_warehouse"
EXTRA_LAUNCH=""
for arg in "${LAUNCH_ARGS[@]+"${LAUNCH_ARGS[@]}"}"; do
  if [[ "$arg" == world:=* ]]; then
    WORLD="${arg#world:=}"
  else
    EXTRA_LAUNCH+=" $arg"
  fi
done

# ── Run simulation ────────────────────────────────────────────────────────────
echo "==> Launching rbot simulation:"
echo "    World  : $WORLD"
echo "    Headless: $HEADLESS"
[[ -n "$EXTRA_LAUNCH" ]] && echo "    Extra args: $EXTRA_LAUNCH"
echo ""

if [[ "$HEADLESS" == true ]]; then
  # Headless: Gazebo server only (no GUI), useful for testing
  docker run --rm -it \
    --network host \
    --ipc host \
    --device /dev/dri \
    --group-add video \
    -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    -e GZ_HEADLESS_RENDERING=1 \
    -e GZ_SIM_RESOURCE_PATH=/ros2_ws/install/rlai_gazebo/share/rlai_gazebo:/ros2_ws/install/rlai_meshes/share \
    "$IMAGE_NAME" \
    ros2 launch rlai_gazebo gazebo.launch.py \
      world:="$WORLD" \
      lidar_2d_enabled:=true \
      depth_camera_enabled:=true \
      imu_enabled:=true \
      ${EXTRA_LAUNCH}
else
  # GUI: forward X11
  docker run --rm -it \
    --network host \
    --ipc host \
    --device /dev/dri \
    --group-add video \
    -e DISPLAY="${DISPLAY:-:0}" \
    -e XAUTHORITY=/tmp/.docker.xauth \
    -e QT_X11_NO_MITSHM=1 \
    -e RMW_IMPLEMENTATION=rmw_cyclonedds_cpp \
    -e GZ_SIM_RESOURCE_PATH=/ros2_ws/install/rlai_gazebo/share/rlai_gazebo:/ros2_ws/install/rlai_meshes/share \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v /tmp/.docker.xauth:/tmp/.docker.xauth:rw \
    "$IMAGE_NAME" \
    ros2 launch rlai_gazebo gazebo.launch.py \
      world:="$WORLD" \
      lidar_2d_enabled:=true \
      depth_camera_enabled:=true \
      imu_enabled:=true \
      ${EXTRA_LAUNCH}
fi
