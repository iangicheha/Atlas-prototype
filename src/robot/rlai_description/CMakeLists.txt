cmake_minimum_required(VERSION 3.8)
project(rlai_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf config launch rviz meshes usd
  DESTINATION share/${PROJECT_NAME}
  OPTIONAL
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
