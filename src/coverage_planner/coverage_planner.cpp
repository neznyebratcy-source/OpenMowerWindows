#include "coverage_planner/coverage_planner.hpp"
#include "coverage_planner/astar.hpp"

#include <nav2_util/node_utils.hpp>
#include <nav2_costmap_2d/cost_values.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/utils.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

#include <algorithm>
#include <cmath>
#include <limits>

// Register this class as a nav2_core::GlobalPlanner plugin so pluginlib can
// load it by name "open_mower_next::coverage_planner::CoveragePlanner".
PLUGINLIB_EXPORT_CLASS(
  open_mower_next::coverage_planner::CoveragePlanner,
  nav2_core::GlobalPlanner)

namespace open_mower_next::coverage_planner
{

// ── Lifecycle ──────────────────────────────────────────────────────────────────

void CoveragePlanner::configure(
  const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
  std::string name,
  std::shared_ptr<tf2_ros::Buffer> /*tf*/,
  std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros)
{
  node_         = parent;
  name_         = name;
  costmap_ros_  = costmap_ros;
  costmap_      = costmap_ros_->getCostmap();
  global_frame_ = costmap_ros_->getGlobalFrameID();

  auto node = node_.lock();

  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".mowing_spacing", rclcpp::ParameterValue(0.4));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".perimeter_passes", rclcpp::ParameterValue(1));

  node->get_parameter(name_ + ".mowing_spacing",   mowing_spacing_);
  node->get_parameter(name_ + ".perimeter_passes",  perimeter_passes_);

  RCLCPP_INFO(
    node->get_logger(),
    "[CoveragePlanner] Configured — strip spacing: %.2f m, perimeter passes: %d",
    mowing_spacing_, perimeter_passes_);

  // Subscribe to the OpenMower map topic; transient_local so we get the last
  // published map even if we subscribe after it was first published.
  // Note: map_server_node remaps its "map" output to "mowing_map"
  map_sub_ = node->create_subscription<open_mower_next::msg::Map>(
    "/mowing_map",
    rclcpp::QoS(1).transient_local(),
    [this](const open_mower_next::msg::Map::SharedPtr msg) {
      std::lock_guard<std::mutex> lock(map_mutex_);
      current_map_ = *msg;
      RCLCPP_DEBUG(
        rclcpp::get_logger("CoveragePlanner"),
        "Map updated: %zu areas", current_map_.areas.size());
    });
}

void CoveragePlanner::cleanup()    { map_sub_.reset(); }
void CoveragePlanner::activate()   {}
void CoveragePlanner::deactivate() {}

// ── createPlan ─────────────────────────────────────────────────────────────────

nav_msgs::msg::Path CoveragePlanner::createPlan(
  const geometry_msgs::msg::PoseStamped & start,
  const geometry_msgs::msg::PoseStamped & goal,
  std::function<bool()> cancel_checker)
{
  nav_msgs::msg::Path path;
  path.header.frame_id = global_frame_;
  path.header.stamp    = node_.lock()->get_clock()->now();

  // ── 1. Pick the operation area closest to the goal pose ─────────────────
  geometry_msgs::msg::Polygon op_polygon;
  bool found = false;
  double best_dist = std::numeric_limits<double>::max();

  {
    std::lock_guard<std::mutex> lock(map_mutex_);
    for (const auto & area : current_map_.areas) {
      if (area.type != open_mower_next::msg::Area::TYPE_OPERATION) { continue; }
      const auto & pts = area.area.polygon.points;
      if (pts.empty()) { continue; }

      // Use centroid distance as selection metric
      double cx = 0.0, cy = 0.0;
      for (const auto & p : pts) { cx += p.x; cy += p.y; }
      cx /= static_cast<double>(pts.size());
      cy /= static_cast<double>(pts.size());

      double d = std::hypot(goal.pose.position.x - cx, goal.pose.position.y - cy);
      if (d < best_dist) {
        best_dist = d;
        op_polygon = area.area.polygon;
        found = true;
      }
    }
  }

  if (!found) {
    RCLCPP_WARN(
      rclcpp::get_logger("CoveragePlanner"),
      "No operation area found in the map — cannot generate coverage path. "
      "Make sure you have recorded and saved at least one TYPE_OPERATION area.");
    return path;
  }

  // ── 2. Generate ordered coverage waypoints ───────────────────────────────
  auto waypoints = generateCoverageWaypoints(op_polygon);
  if (waypoints.empty()) {
    RCLCPP_WARN(rclcpp::get_logger("CoveragePlanner"), "No waypoints generated.");
    return path;
  }
  RCLCPP_INFO(
    rclcpp::get_logger("CoveragePlanner"),
    "Coverage path: %zu waypoints over %.1f m² area.",
    waypoints.size(), best_dist);

  // ── 3. Build path: start → wp[0] → wp[1] → … with A* obstacle detours ──
  path.poses.push_back(start);

  // Helper: build a stamped pose from a Point + yaw
  auto make_pose = [&](const geometry_msgs::msg::Point & pt, double yaw) {
    geometry_msgs::msg::PoseStamped ps;
    ps.header           = path.header;
    ps.pose.position    = pt;
    ps.pose.orientation = yawToQuaternion(yaw);
    return ps;
  };

  // start → first waypoint
  {
    double dir = std::atan2(
      waypoints[0].y - start.pose.position.y,
      waypoints[0].x - start.pose.position.x);
    auto seg = connectWithAstar(start, make_pose(waypoints[0], dir), cancel_checker);
    path.poses.insert(path.poses.end(), seg.begin(), seg.end());
  }

  // Consecutive waypoints
  for (size_t i = 1; i < waypoints.size(); i++) {
    if (cancel_checker()) {
      RCLCPP_INFO(rclcpp::get_logger("CoveragePlanner"), "Planning cancelled.");
      return path;
    }
    double dir = std::atan2(
      waypoints[i].y - waypoints[i - 1].y,
      waypoints[i].x - waypoints[i - 1].x);
    auto seg = connectWithAstar(
      make_pose(waypoints[i - 1], dir),
      make_pose(waypoints[i],     dir),
      cancel_checker);
    path.poses.insert(path.poses.end(), seg.begin(), seg.end());
  }

  RCLCPP_INFO(
    rclcpp::get_logger("CoveragePlanner"),
    "Coverage path built: %zu poses total.", path.poses.size());
  return path;
}

// ── Coverage waypoint generation ───────────────────────────────────────────────

std::vector<geometry_msgs::msg::Point> CoveragePlanner::generateCoverageWaypoints(
  const geometry_msgs::msg::Polygon & polygon)
{
  std::vector<geometry_msgs::msg::Point> waypoints;
  if (polygon.points.size() < 3) { return waypoints; }

  // ── Phase 1: Perimeter pass(es) ──────────────────────────────────────────
  // Walk the polygon vertices in order to cleanly cut the boundary first.
  for (int pass = 0; pass < perimeter_passes_; pass++) {
    for (const auto & pt : polygon.points) {
      geometry_msgs::msg::Point p;
      p.x = pt.x; p.y = pt.y; p.z = 0.0;
      waypoints.push_back(p);
    }
    // Close the loop back to the first vertex
    geometry_msgs::msg::Point first;
    first.x = polygon.points[0].x;
    first.y = polygon.points[0].y;
    first.z = 0.0;
    waypoints.push_back(first);
  }

  // ── Phase 2: Boustrophedon (snake) interior ──────────────────────────────
  float min_y =  std::numeric_limits<float>::max();
  float max_y = -std::numeric_limits<float>::max();
  for (const auto & pt : polygon.points) {
    min_y = std::min(min_y, pt.y);
    max_y = std::max(max_y, pt.y);
  }

  bool left_to_right = true;
  for (double y = min_y; y <= max_y + 1e-6; y += mowing_spacing_) {
    auto xs = scanLineIntersections(polygon, y);
    if (xs.empty()) {
      left_to_right = !left_to_right;
      continue;
    }

    // Sort intersections; take all as strip entry/exit x-values
    std::sort(xs.begin(), xs.end());
    if (!left_to_right) { std::reverse(xs.begin(), xs.end()); }

    for (double x : xs) {
      geometry_msgs::msg::Point p;
      p.x = x; p.y = y; p.z = 0.0;
      waypoints.push_back(p);
    }
    left_to_right = !left_to_right;
  }

  return waypoints;
}

// ── Scan-line polygon intersection ────────────────────────────────────────────

std::vector<double> CoveragePlanner::scanLineIntersections(
  const geometry_msgs::msg::Polygon & polygon, double y)
{
  std::vector<double> xs;
  const auto & pts = polygon.points;
  const size_t n   = pts.size();

  for (size_t i = 0; i < n; i++) {
    const auto & p1 = pts[i];
    const auto & p2 = pts[(i + 1) % n];

    // Edge crosses y (strict on one side to avoid double-counting vertices)
    if ((p1.y <= y && p2.y > y) || (p2.y <= y && p1.y > y)) {
      double t = (y - p1.y) / (p2.y - p1.y);
      xs.push_back(static_cast<double>(p1.x) + t * (p2.x - p1.x));
    }
  }
  return xs;
}

// ── Obstacle-aware segment routing ─────────────────────────────────────────────

std::vector<geometry_msgs::msg::PoseStamped> CoveragePlanner::connectWithAstar(
  const geometry_msgs::msg::PoseStamped & from,
  const geometry_msgs::msg::PoseStamped & to,
  const std::function<bool()> & cancel_checker)
{
  if (cancel_checker()) { return {}; }

  // Lock the costmap once for the entire call (both line-check and A* search)
  costmap_ = costmap_ros_->getCostmap();
  std::lock_guard<nav2_costmap_2d::Costmap2D::mutex_t> lock(*(costmap_->getMutex()));

  if (isLineClearLocked(
    from.pose.position.x, from.pose.position.y,
    to.pose.position.x,   to.pose.position.y))
  {
    // Happy path: straight line, no obstacles
    return interpolateLine(from, to);
  }

  // Blocked — find a detour with A* on the global costmap
  unsigned int sx_u, sy_u, gx_u, gy_u;
  const bool start_ok =
    costmap_->worldToMap(from.pose.position.x, from.pose.position.y, sx_u, sy_u);
  const bool goal_ok  =
    costmap_->worldToMap(to.pose.position.x,   to.pose.position.y,   gx_u, gy_u);

  if (!start_ok || !goal_ok) {
    RCLCPP_WARN(
      rclcpp::get_logger("CoveragePlanner"),
      "Waypoint outside costmap bounds — falling back to straight line.");
    return interpolateLine(from, to);
  }

  auto grid_path = aStarGrid(
    costmap_,
    static_cast<int>(sx_u), static_cast<int>(sy_u),
    static_cast<int>(gx_u), static_cast<int>(gy_u));

  if (grid_path.empty()) {
    RCLCPP_WARN(
      rclcpp::get_logger("CoveragePlanner"),
      "A* could not find a path around the obstacle — using straight line.");
    return interpolateLine(from, to);
  }

  // Convert grid cells back to world-frame stamped poses
  std::vector<geometry_msgs::msg::PoseStamped> poses;
  poses.reserve(grid_path.size());

  for (size_t i = 0; i < grid_path.size(); i++) {
    double wx, wy;
    costmap_->mapToWorld(
      static_cast<unsigned int>(grid_path[i].first),
      static_cast<unsigned int>(grid_path[i].second),
      wx, wy);

    // Orientation: point toward the next cell; use goal yaw on the last cell
    double yaw = 0.0;
    if (i + 1 < grid_path.size()) {
      double nx, ny;
      costmap_->mapToWorld(
        static_cast<unsigned int>(grid_path[i + 1].first),
        static_cast<unsigned int>(grid_path[i + 1].second),
        nx, ny);
      yaw = std::atan2(ny - wy, nx - wx);
    } else {
      yaw = tf2::getYaw(to.pose.orientation);
    }

    geometry_msgs::msg::PoseStamped ps;
    ps.header           = from.header;
    ps.pose.position.x  = wx;
    ps.pose.position.y  = wy;
    ps.pose.position.z  = 0.0;
    ps.pose.orientation = yawToQuaternion(yaw);
    poses.push_back(ps);
  }
  return poses;
}

// ── Line-of-sight check (Bresenham) ───────────────────────────────────────────

bool CoveragePlanner::isLineClearLocked(double x1, double y1, double x2, double y2)
{
  // Caller must already hold costmap_->getMutex()
  unsigned int mx1, my1, mx2, my2;
  if (!costmap_->worldToMap(x1, y1, mx1, my1)) { return false; }
  if (!costmap_->worldToMap(x2, y2, mx2, my2)) { return false; }

  int sx = static_cast<int>(mx1), sy = static_cast<int>(my1);
  int ex = static_cast<int>(mx2), ey = static_cast<int>(my2);
  int dx = std::abs(ex - sx), dy = std::abs(ey - sy);
  int step_x = (sx < ex) ? 1 : -1;
  int step_y = (sy < ey) ? 1 : -1;
  int err = dx - dy;
  int x = sx, y = sy;

  while (true) {
    if (costmap_->getCost(
          static_cast<unsigned int>(x),
          static_cast<unsigned int>(y)) >= nav2_costmap_2d::LETHAL_OBSTACLE)
    {
      return false;
    }
    if (x == ex && y == ey) { break; }
    int e2 = 2 * err;
    if (e2 > -dy) { err -= dy; x += step_x; }
    if (e2 <  dx) { err += dx; y += step_y; }
  }
  return true;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

std::vector<geometry_msgs::msg::PoseStamped> CoveragePlanner::interpolateLine(
  const geometry_msgs::msg::PoseStamped & from,
  const geometry_msgs::msg::PoseStamped & to,
  double step)
{
  const double dx   = to.pose.position.x - from.pose.position.x;
  const double dy   = to.pose.position.y - from.pose.position.y;
  const double dist = std::hypot(dx, dy);
  const double yaw  = std::atan2(dy, dx);

  std::vector<geometry_msgs::msg::PoseStamped> poses;
  const int steps = std::max(1, static_cast<int>(dist / step));
  poses.reserve(steps + 1);

  for (int i = 0; i <= steps; i++) {
    double t = static_cast<double>(i) / static_cast<double>(steps);
    geometry_msgs::msg::PoseStamped ps;
    ps.header           = from.header;
    ps.pose.position.x  = from.pose.position.x + t * dx;
    ps.pose.position.y  = from.pose.position.y + t * dy;
    ps.pose.position.z  = 0.0;
    ps.pose.orientation = yawToQuaternion(yaw);
    poses.push_back(ps);
  }
  return poses;
}

geometry_msgs::msg::Quaternion CoveragePlanner::yawToQuaternion(double yaw)
{
  tf2::Quaternion q;
  q.setRPY(0.0, 0.0, yaw);
  return tf2::toMsg(q);
}

}  // namespace open_mower_next::coverage_planner