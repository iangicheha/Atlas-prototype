cmake_minimum_required(VERSION 3.8)
project(rlai_lidar_processing)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

# Workaround: ros-humble-pcl-ros exports VTK::GUISupportQt and Boost::date_time
# in its INTERFACE_LINK_LIBRARIES even when those components are not needed by
# this package.  Create minimal IMPORTED INTERFACE stubs so CMake's target-
# validation step succeeds without pulling in the Qt/VTK/Boost SDKs.
find_package(Boost QUIET COMPONENTS date_time)
if(NOT Boost_date_time_FOUND AND NOT TARGET Boost::date_time)
  add_library(Boost::date_time IMPORTED INTERFACE)
endif()
find_package(VTK QUIET)
if(NOT TARGET VTK::GUISupportQt)
  add_library(VTK::GUISupportQt IMPORTED INTERFACE)
endif()

find_package(pcl_ros REQUIRED)
find_package(pcl_conversions REQUIRED)

add_executable(pointcloud_filter_node
  src/pointcloud_filter_node.cpp)

target_include_directories(pointcloud_filter_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)

target_compile_features(pointcloud_filter_node PUBLIC cxx_std_17)

ament_target_dependencies(pointcloud_filter_node
  rclcpp
  sensor_msgs
  pcl_ros
  pcl_conversions)

install(TARGETS pointcloud_filter_node
  DESTINATION lib/${PROJECT_NAME})

install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME})

ament_package()
