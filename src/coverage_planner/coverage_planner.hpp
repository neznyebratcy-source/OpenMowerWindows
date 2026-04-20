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

// Nav2 GlobalPlanner plugin that generates a full boustrophedon (snake) coverage
// path over the nearest operation area polygon, then connects each pair of
// consecutive strip endpoints with either a straight line (when obstacle-free) or
// an A* detour around blocked cells in the global costmap.
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

  // Returns ordered waypoints: perimeter passes first, then boustrophedon interior.
  std::vector<geometry_msgs::msg::Point> generateCoverageWaypoints(
    const geometry_msgs::msg::Polygon & polygon);

  // Computes x-coordinates where a horizontal scan line at y intersects polygon edges.
  std::vector<double> scanLineIntersections(
    const geometry_msgs::msg::Polygon & polygon, double y);

  // ── Obstacle-aware segment routing ───────────────────────────────────────

  // Returns a path segment from `from` to `to`.
  // Uses straight-line interpolation when the line is clear; falls back to A*
  // when an obstacle is detected. The costmap mutex must NOT be held by the caller.
  std::vector<geometry_msgs::msg::PoseStamped> connectWithAstar(
    const geometry_msgs::msg::PoseStamped & from,
    const geometry_msgs::msg::PoseStamped & to,
    const std::function<bool()> & cancel_checker);

  // Walks the straight line using Bresenham's algorithm; returns false if any cell
  // has cost >= LETHAL_OBSTACLE.  Caller must hold the costmap mutex.
  bool isLineClearLocked(double x1, double y1, double x2, double y2);

  // Densely interpolates world-frame poses along a straight line at `step` metres.
  std::vector<geometry_msgs::msg::PoseStamped> interpolateLine(
    const geometry_msgs::msg::PoseStamped & from,
    const geometry_msgs::msg::PoseStamped & to,
    double step = 0.05);

  // Converts a yaw angle (radians) to a geometry_msgs Quaternion.
  static geometry_msgs::msg::Quaternion yawToQuaternion(double yaw);

  // ── State ─────────────────────────────────────────────────────────────────
  double mowing_spacing_{0.4};   // Strip spacing in metres (= cutting width)
  int perimeter_passes_{1};       // How many perimeter laps before interior fill

  std::string name_;
  std::string global_frame_;

  rclcpp_lifecycle::LifecycleNode::WeakPtr              node_;
  std::shared_ptr<nav2_costmap_2d::Costmap2DROS>        costmap_ros_;
  nav2_costmap_2d::Costmap2D *                          costmap_{nullptr};

  // Receives the OpenMower area map to obtain operation-area polygons
  rclcpp::Subscription<open_mower_next::msg::Map>::SharedPtr map_sub_;
  open_mower_next::msg::Map                             current_map_;
  std::mutex                                            map_mutex_;
};

}  // namespace open_mower_next::coverage_planner