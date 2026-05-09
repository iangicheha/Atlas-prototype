#!/bin/bash
# scripts/install_deps.sh
# Installs all system-level dependencies for rbot on Ubuntu 24.04 (native).
# Run once on a fresh machine before building the workspace.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(dirname "$SCRIPT_DIR")"

echo "==> Adding ROS 2 apt repository"
sudo apt-get update
sudo apt-get install -y curl gnupg lsb-release

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

echo "==> Installing ROS 2 Jazzy base + tooling"
sudo apt-get update && sudo apt-get install -y \
    ros-jazzy-ros-base \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-nav2-bringup \
    ros-jazzy-nav2-mppi-controller \
    ros-jazzy-nav2-smac-planner \
    ros-jazzy-slam-toolbox \
    ros-jazzy-robot-localization \
    ros-jazzy-imu-filter-madgwick \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-teleop-twist-joy \
    ros-jazzy-joy \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-pcl-ros \
    ros-jazzy-image-transport \
    ros-jazzy-image-proc \
    ros-jazzy-depth-image-proc \
    ros-jazzy-cv-bridge \
    ros-jazzy-stereo-image-proc \
    ros-jazzy-topic-based-ros2-control \
    ros-jazzy-rviz2 \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-vcstool \
    python3-pip

echo "==> Adding Gazebo Harmonic apt repository"
sudo curl -sSL https://packages.osrfoundation.org/gazebo.gpg \
    -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
    http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

sudo apt-get update && sudo apt-get install -y \
    gz-harmonic \
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control

echo "==> Initialising rosdep"
sudo rosdep init 2>/dev/null || true
rosdep update

echo "==> Running rosdep install for workspace packages"
cd "$WS_ROOT"
rosdep install --from-paths src --ignore-src -r -y \
    --skip-keys "ament_python teleop_twist_joy joy"

echo ""
echo "All dependencies installed. Run 'bash scripts/build.sh' to build the workspace."
