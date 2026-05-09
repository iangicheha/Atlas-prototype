// Filters raw VLP-16 point clouds by height, then voxel-downsamples for downstream perception.

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <pcl_ros/transforms.hpp>
#include <pcl/filters/voxel_grid.h>
#include <pcl/filters/passthrough.h>
#include <pcl_conversions/pcl_conversions.h>

class PointCloudFilterNode : public rclcpp::Node
{
public:
  PointCloudFilterNode()
  : Node("pointcloud_filter")
  {
    declare_parameter<double>("leaf_size", 0.05);
    declare_parameter<double>("z_min",    -0.10);
    declare_parameter<double>("z_max",     2.00);

    sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      "/lidar_3d/points_raw",
      rclcpp::SensorDataQoS(),
      std::bind(&PointCloudFilterNode::callback, this, std::placeholders::_1));

    pub_ = create_publisher<sensor_msgs::msg::PointCloud2>("/lidar_3d/points", 10);

    RCLCPP_INFO(get_logger(),
      "pointcloud_filter started — leaf=%.3fm z=[%.2f, %.2f]",
      get_parameter("leaf_size").as_double(),
      get_parameter("z_min").as_double(),
      get_parameter("z_max").as_double());
  }

private:
  void callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
    pcl::fromROSMsg(*msg, *cloud);

    if (cloud->empty()) {
      return;
    }

    // Remove points outside the configured vertical obstacle band.
    pcl::PassThrough<pcl::PointXYZ> pass;
    pass.setInputCloud(cloud);
    pass.setFilterFieldName("z");
    pass.setFilterLimits(
      static_cast<float>(get_parameter("z_min").as_double()),
      static_cast<float>(get_parameter("z_max").as_double()));
    pass.filter(*cloud);

    // Downsample to reduce point density before publishing.
    pcl::VoxelGrid<pcl::PointXYZ> vg;
    vg.setInputCloud(cloud);
    auto leaf = static_cast<float>(get_parameter("leaf_size").as_double());
    vg.setLeafSize(leaf, leaf, leaf);
    vg.filter(*cloud);

    sensor_msgs::msg::PointCloud2 out_msg;
    pcl::toROSMsg(*cloud, out_msg);
    out_msg.header = msg->header;
    pub_->publish(out_msg);
  }

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<PointCloudFilterNode>());
  rclcpp::shutdown();
  return 0;
}
