#include "coverage_planner/coverage_planner.hpp"
#include "coverage_planner/astar.hpp"
#include <nav2_costmap_2d/cost_values.hpp>

#include <nav2_util/node_utils.hpp>
#include <tf2/LinearMath/Quaternion.h>
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
  global_frame_ = costmap_ros_->getGlobalFrameID();

  auto node = node_.lock();

  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".mowing_spacing", rclcpp::ParameterValue(0.4));
  nav2_util::declare_parameter_if_not_declared(
    node, name_ + ".robot_radius", rclcpp::ParameterValue(0.5));

  node->get_parameter(name_ + ".mowing_spacing", mowing_spacing_);
  node->get_parameter(name_ + ".robot_radius",   robot_radius_);

  RCLCPP_INFO(
    node->get_logger(),
    "[CoveragePlanner] Configured — strip spacing: %.2f m, robot radius: %.2f m",
    mowing_spacing_, robot_radius_);

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
    throw std::runtime_error(
      "CoveragePlanner: no operation area found near the goal — "
      "is the mowing map loaded? (/mowing_map topic)");
  }

  // Find the nearest point on any polygon edge to the robot start — used only
  // to decide which end of the first snake strip to approach first.
  geometry_msgs::msg::Point32 snake_entry;
  snake_entry.x = static_cast<float>(start.pose.position.x);
  snake_entry.y = static_cast<float>(start.pose.position.y);
  snake_entry.z = 0.0f;
  {
    const size_t n = op_polygon.points.size();
    double best_d = std::numeric_limits<double>::max();
    for (size_t i = 0; i < n; i++) {
      const auto & p1 = op_polygon.points[i];
      const auto & p2 = op_polygon.points[(i + 1) % n];
      double ex = p2.x - p1.x, ey = p2.y - p1.y;
      double len2 = ex * ex + ey * ey;
      if (len2 < 1e-9) { continue; }
      double t = std::clamp(
        ((start.pose.position.x - p1.x) * ex +
         (start.pose.position.y - p1.y) * ey) / len2, 0.0, 1.0);
      double px = p1.x + t * ex, py = p1.y + t * ey;
      double d  = std::hypot(start.pose.position.x - px,
                             start.pose.position.y - py);
      if (d < best_d) {
        best_d = d;
        snake_entry.x = static_cast<float>(px);
        snake_entry.y = static_cast<float>(py);
      }
    }
  }

  // ── 2. Generate ordered coverage waypoints ───────────────────────────────
  auto waypoints = generateCoverageWaypoints(op_polygon, snake_entry);
  if (waypoints.empty()) {
    throw std::runtime_error(
      "CoveragePlanner: no coverage waypoints generated — "
      "check mowing_spacing and polygon size.");
  }
  RCLCPP_INFO(
    rclcpp::get_logger("CoveragePlanner"),
    "Coverage path: %zu waypoints over %.1f m² area.",
    waypoints.size(), best_dist);

  // ── 3. Build path: start → wp[0] → wp[1] → … straight lines ────────────
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
    auto seg = routeSegment(start, make_pose(waypoints[0], dir));
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
    auto seg = routeSegment(
      make_pose(waypoints[i - 1], dir),
      make_pose(waypoints[i],     dir));
    path.poses.insert(path.poses.end(), seg.begin(), seg.end());
  }

  RCLCPP_INFO(
    rclcpp::get_logger("CoveragePlanner"),
    "Coverage path built: %zu poses total.", path.poses.size());
  return path;
}

// ── Coverage waypoint generation ───────────────────────────────────────────────

std::vector<geometry_msgs::msg::Point> CoveragePlanner::generateCoverageWaypoints(
  const geometry_msgs::msg::Polygon & polygon,
  const geometry_msgs::msg::Point32 & snake_entry)
{
  std::vector<geometry_msgs::msg::Point> waypoints;
  if (polygon.points.size() < 3) { return waypoints; }

  // ── Boustrophedon sweep with robot_radius inset and smart start direction ──
  float min_y =  std::numeric_limits<float>::max();
  float max_y = -std::numeric_limits<float>::max();
  for (const auto & pt : polygon.points) {
    min_y = std::min(min_y, pt.y);
    max_y = std::max(max_y, pt.y);
  }

  // Phase 1.5: inset first/last strip by robot_radius so the robot body
  // stays fully inside the polygon boundary on every strip.
  double eff_min_y = static_cast<double>(min_y) + robot_radius_;
  double eff_max_y = static_cast<double>(max_y) - robot_radius_;
  if (eff_min_y >= eff_max_y) { return waypoints; }

  // Phase 2: pick the nearest polygon boundary to the robot as the start of
  // the sweep.  Starting close to the robot minimises the initial approach.
  double mid_y    = (eff_min_y + eff_max_y) * 0.5;
  bool   sweep_up = (static_cast<double>(snake_entry.y) <= mid_y);
  double y_start  = sweep_up ? eff_min_y : eff_max_y;
  double y_end    = sweep_up ? eff_max_y : eff_min_y;
  double y_step   = sweep_up ? mowing_spacing_ : -mowing_spacing_;

  // Determine which end of the first strip is closer to the robot.
  bool left_to_right = true;
  {
    auto xs0 = scanLineIntersections(polygon, y_start);
    if (xs0.size() >= 2) {
      std::sort(xs0.begin(), xs0.end());
      double x_left  = xs0.front() + robot_radius_;
      double x_right = xs0.back()  - robot_radius_;
      if (x_left < x_right) {
        double d_left  = std::hypot(snake_entry.x - x_left,  snake_entry.y - y_start);
        double d_right = std::hypot(snake_entry.x - x_right, snake_entry.y - y_start);
        left_to_right  = (d_left <= d_right);
      }
    }
  }

  for (double y = y_start;
       sweep_up ? (y <= y_end + 1e-6) : (y >= y_end - 1e-6);
       y += y_step) {
    auto xs = scanLineIntersections(polygon, y);
    if (xs.size() < 2) { continue; }

    std::sort(xs.begin(), xs.end());

    // Phase 1.5: inset strip endpoints so robot body stays inside polygon.
    xs.front() += robot_radius_;
    xs.back()  -= robot_radius_;
    if (xs.front() >= xs.back()) { continue; }

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

// ── Obstacle-aware segment routing ────────────────────────────────────────────

bool CoveragePlanner::lineClear(
  nav2_costmap_2d::Costmap2D * costmap,
  const geometry_msgs::msg::PoseStamped & from,
  const geometry_msgs::msg::PoseStamped & to)
{
  const double dx   = to.pose.position.x - from.pose.position.x;
  const double dy   = to.pose.position.y - from.pose.position.y;
  const double dist = std::hypot(dx, dy);
  const int    steps = std::max(2, static_cast<int>(dist / costmap->getResolution()));

  for (int i = 0; i <= steps; i++) {
    const double t  = static_cast<double>(i) / static_cast<double>(steps);
    unsigned int mx, my;
    if (!costmap->worldToMap(
          from.pose.position.x + t * dx,
          from.pose.position.y + t * dy, mx, my)) { continue; }
    if (costmap->getCost(mx, my) >= nav2_costmap_2d::INSCRIBED_INFLATED_OBSTACLE) { return false; }
  }
  return true;
}

std::vector<geometry_msgs::msg::PoseStamped> CoveragePlanner::routeSegment(
  const geometry_msgs::msg::PoseStamped & from,
  const geometry_msgs::msg::PoseStamped & to)
{
  auto * costmap = costmap_ros_->getCostmap();
  std::unique_lock<nav2_costmap_2d::Costmap2D::mutex_t> lock(*costmap->getMutex());

  if (lineClear(costmap, from, to)) {
    return interpolateLine(from, to);
  }

  // Straight line is blocked — try A*
  unsigned int sx, sy, gx, gy;
  if (!costmap->worldToMap(from.pose.position.x, from.pose.position.y, sx, sy) ||
      !costmap->worldToMap(to.pose.position.x,   to.pose.position.y,   gx, gy)) {
    return interpolateLine(from, to);
  }

  const auto cells = aStarGrid(
    costmap,
    static_cast<int>(sx), static_cast<int>(sy),
    static_cast<int>(gx), static_cast<int>(gy));

  if (cells.empty()) {
    RCLCPP_WARN(rclcpp::get_logger("CoveragePlanner"),
      "A* found no path between (%.2f,%.2f) and (%.2f,%.2f) — using straight line.",
      from.pose.position.x, from.pose.position.y,
      to.pose.position.x,   to.pose.position.y);
    return interpolateLine(from, to);
  }

  RCLCPP_DEBUG(rclcpp::get_logger("CoveragePlanner"),
    "A* routed %zu cells around obstacle.", cells.size());

  std::vector<geometry_msgs::msg::PoseStamped> poses;
  poses.reserve(cells.size());

  const double fallback_yaw = std::atan2(
    to.pose.position.y - from.pose.position.y,
    to.pose.position.x - from.pose.position.x);

  for (size_t i = 0; i < cells.size(); i++) {
    double wx, wy;
    costmap->mapToWorld(
      static_cast<unsigned int>(cells[i].first),
      static_cast<unsigned int>(cells[i].second),
      wx, wy);

    double yaw = fallback_yaw;
    if (i + 1 < cells.size()) {
      double nwx, nwy;
      costmap->mapToWorld(
        static_cast<unsigned int>(cells[i + 1].first),
        static_cast<unsigned int>(cells[i + 1].second),
        nwx, nwy);
      yaw = std::atan2(nwy - wy, nwx - wx);
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

}  // namespace open_mower_next::coverage_planner