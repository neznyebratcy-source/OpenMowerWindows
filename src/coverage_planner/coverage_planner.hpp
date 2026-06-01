#pragma once

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_lifecycle/lifecycle_node.hpp>
#include <nav2_core/global_planner.hpp>
#include <nav2_costmap_2d/costmap_2d_ros.hpp>
#include <nav2_costmap_2d/costmap_2d.hpp>
#include <nav_msgs/msg/path.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <geometry_msgs/msg/polygon.hpp>
#include <geometry_msgs/msg/quaternion.hpp>
#include <tf2_ros/buffer.h>
#include <pluginlib/class_list_macros.hpp>

#include "open_mower_next/msg/map.hpp"

#include <mutex>
#include <string>
#include <vector>

namespace open_mower_next::coverage_planner
{

// Nav2 GlobalPlanner plugin that generates a boustrophedon (snake) coverage path
// over the nearest operation area polygon.  Each strip runs edge-to-edge across
// the polygon with straight-line interpolation between endpoints.
class CoveragePlanner : public nav2_core::GlobalPlanner
{
public:
  CoveragePlanner()  = default;
  ~CoveragePlanner() override = default;

  // ── Nav2 GlobalPlanner interface ──────────────────────────────────────────
  void configure(
    const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
    std::string name,
    std::shared_ptr<tf2_ros::Buffer> tf,
    std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros) override;

  void cleanup()    override;
  void activate()   override;
  void deactivate() override;

  // Entry point called by the Nav2 planner server.
  // Uses goal position to identify the nearest operation area, then returns
  // the complete coverage path from start through all mowing strips.
  // cancel_checker is polled during planning so Nav2 can abort a slow plan.
  nav_msgs::msg::Path createPlan(
    const geometry_msgs::msg::PoseStamped & start,
    const geometry_msgs::msg::PoseStamped & goal,
    std::function<bool()> cancel_checker) override;

private:
  // ── Coverage path generation ──────────────────────────────────────────────

  // Returns boustrophedon (snake) waypoints covering the entire polygon edge-to-edge.
  // snake_entry: the robot's nearest point on the polygon boundary, used to pick
  // which end of the first strip to start from (minimises the initial approach).
  std::vector<geometry_msgs::msg::Point> generateCoverageWaypoints(
    const geometry_msgs::msg::Polygon & polygon,
    const geometry_msgs::msg::Point32 & snake_entry);

  // Computes x-coordinates where a horizontal scan line at y intersects polygon edges.
  std::vector<double> scanLineIntersections(
    const geometry_msgs::msg::Polygon & polygon, double y);

  // ── Path interpolation ────────────────────────────────────────────────────

  // Densely interpolates world-frame poses along a straight line at `step` metres.
  std::vector<geometry_msgs::msg::PoseStamped> interpolateLine(
    const geometry_msgs::msg::PoseStamped & from,
    const geometry_msgs::msg::PoseStamped & to,
    double step = 0.05);

  // Routes from→to avoiding lethal costmap cells.
  // Uses A* when the straight line is blocked; falls back to interpolateLine otherwise.
  std::vector<geometry_msgs::msg::PoseStamped> routeSegment(
    const geometry_msgs::msg::PoseStamped & from,
    const geometry_msgs::msg::PoseStamped & to);

  // Returns true if the straight line from→to contains no lethal costmap cells.
  bool lineClear(
    nav2_costmap_2d::Costmap2D * costmap,
    const geometry_msgs::msg::PoseStamped & from,
    const geometry_msgs::msg::PoseStamped & to);

  // Converts a yaw angle (radians) to a geometry_msgs Quaternion.
  static geometry_msgs::msg::Quaternion yawToQuaternion(double yaw);

  // ── State ─────────────────────────────────────────────────────────────────
  double mowing_spacing_{0.4};   // Strip spacing in metres (= cutting width)
  double robot_radius_{0.5};     // Inset from polygon edges so robot body stays inside

  std::string name_;
  std::string global_frame_;

  rclcpp_lifecycle::LifecycleNode::WeakPtr              node_;
  std::shared_ptr<nav2_costmap_2d::Costmap2DROS>        costmap_ros_;

  // Receives the OpenMower area map to obtain operation-area polygons
  rclcpp::Subscription<open_mower_next::msg::Map>::SharedPtr map_sub_;
  open_mower_next::msg::Map                             current_map_;
  std::mutex                                            map_mutex_;
};

}  // namespace open_mower_next::coverage_planner