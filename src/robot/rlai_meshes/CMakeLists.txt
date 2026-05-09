cmake_minimum_required(VERSION 3.8)
project(rlai_meshes)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY meshes
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

ament_package()
