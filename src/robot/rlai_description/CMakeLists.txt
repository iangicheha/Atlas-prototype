cmake_minimum_required(VERSION 3.8)
project(rlai_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf config launch rviz meshes usd
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)


ament_package()
