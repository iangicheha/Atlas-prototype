cmake_minimum_required(VERSION 3.8)
project(rlai_gazebo)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY launch worlds config models rviz
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
