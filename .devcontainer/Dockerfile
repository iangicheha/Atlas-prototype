# .devcontainer/Dockerfile
# VS Code devcontainer image — extends the Gazebo simulation image with dev tooling
FROM ros:jazzy-ros-base-noble

ARG DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Simulation and nav stack
RUN apt-get update && apt-get install -y \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-vcstool \
    python3-pip \
    gz-harmonic \
    ros-jazzy-ros-gzharmonic \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-nav2-bringup \
    ros-jazzy-nav2-mppi-controller \
    ros-jazzy-nav2-smac-planner \
    ros-jazzy-slam-toolbox \
    ros-jazzy-robot-localization \
    ros-jazzy-imu-filter-madgwick \
    ros-jazzy-teleop-twist-keyboard \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-pcl-ros \
    ros-jazzy-image-transport \
    ros-jazzy-image-proc \
    ros-jazzy-depth-image-proc \
    ros-jazzy-cv-bridge \
    ros-jazzy-stereo-image-proc \
    ros-jazzy-topic-based-ros2-control \
    # Dev extras
    git \
    bash-completion \
    sudo \
    curl \
    wget \
    vim \
    clang-format \
    python3-pre-commit \
    && rm -rf /var/lib/apt/lists/*

# Allow the default user to run sudo without password
ARG USERNAME=ubuntu
RUN echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /ros2_ws

# Source ROS 2 on every shell
RUN echo ". /opt/ros/jazzy/setup.bash" >> /etc/bash.bashrc && \
    echo ". /ros2_ws/install/setup.bash 2>/dev/null || true" >> /etc/bash.bashrc

ENV COLCON_HOME=/ros2_ws/.colcon
