#pragma once

// Grid-based A* search on a nav2_costmap_2d::Costmap2D.
// Used by CoveragePlanner to route around obstacles between strip endpoints.

#include <nav2_costmap_2d/costmap_2d.hpp>
#include <nav2_costmap_2d/cost_values.hpp>

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <unordered_map>
#include <vector>

namespace open_mower_next::coverage_planner
{

// Returns the grid-cell path [(x,y), ...] from (sx,sy) to (gx,gy).
// Cells with cost >= LETHAL_OBSTACLE are impassable.
// Inflated cells (cost < LETHAL) are passable but penalised so the planner
// naturally prefers open space.
// Returns an empty vector when no path exists or coordinates are out of bounds.
inline std::vector<std::pair<int, int>> aStarGrid(
  nav2_costmap_2d::Costmap2D * costmap,
  int sx, int sy,
  int gx, int gy)
{
  const int W = static_cast<int>(costmap->getSizeInCellsX());
  const int H = static_cast<int>(costmap->getSizeInCellsY());

  // Bounds check
  if (sx < 0 || sx >= W || sy < 0 || sy >= H) return {};
  if (gx < 0 || gx >= W || gy < 0 || gy >= H) return {};

  auto flat = [&](int x, int y) { return y * W + x; };

  // Octile heuristic — admissible for 8-directional movement
  auto heuristic = [](int x1, int y1, int x2, int y2) -> double {
    int dx = std::abs(x2 - x1);
    int dy = std::abs(y2 - y1);
    return (dx + dy) + (std::sqrt(2.0) - 2.0) * std::min(dx, dy);
  };

  struct Node
  {
    int x, y;
    double g, f;
    bool operator>(const Node & o) const { return f > o.f; }
  };

  const int total = W * H;
  std::vector<double> g_cost(total, std::numeric_limits<double>::infinity());
  std::vector<int> parent(total, -1);

  std::priority_queue<Node, std::vector<Node>, std::greater<Node>> open;

  const int s_idx = flat(sx, sy);
  const int g_idx = flat(gx, gy);
  g_cost[s_idx] = 0.0;
  open.push({sx, sy, 0.0, heuristic(sx, sy, gx, gy)});

  // 8-directional movement: dx, dy, base movement cost
  static constexpr int DX[8]     = {-1, 0, 1, -1, 1, -1, 0, 1};
  static constexpr int DY[8]     = {-1, -1, -1, 0, 0, 1, 1, 1};
  static constexpr double MOVE[8] = {
    1.41421, 1.0, 1.41421,
    1.0,          1.0,
    1.41421, 1.0, 1.41421
  };

  while (!open.empty()) {
    Node cur = open.top();
    open.pop();

    const int cur_idx = flat(cur.x, cur.y);

    if (cur_idx == g_idx) {
      // Reconstruct grid-cell path
      std::vector<std::pair<int, int>> path;
      int node = g_idx;
      while (node != -1) {
        path.push_back({node % W, node / W});
        node = parent[node];
      }
      std::reverse(path.begin(), path.end());
      return path;
    }

    // Skip stale priority-queue entries
    if (cur.g > g_cost[cur_idx] + 1e-9) { continue; }

    for (int i = 0; i < 8; i++) {
      const int nx = cur.x + DX[i];
      const int ny = cur.y + DY[i];
      if (nx < 0 || nx >= W || ny < 0 || ny >= H) { continue; }

      const uint8_t cell = costmap->getCost(
        static_cast<unsigned int>(nx), static_cast<unsigned int>(ny));

      // Hard wall — skip
      if (cell >= nav2_costmap_2d::LETHAL_OBSTACLE) { continue; }

      // Inflated zone costs more; INSCRIBED treated as near-lethal
      double extra = 0.0;
      if (cell >= nav2_costmap_2d::INSCRIBED_INFLATED_OBSTACLE) {
        extra = 50.0;  // strongly penalise being this close to an obstacle
      } else if (cell > 0) {
        extra = (static_cast<double>(cell) / 252.0) * 5.0;
      }

      const double new_g = g_cost[cur_idx] + MOVE[i] + extra;
      const int n_idx    = flat(nx, ny);

      if (new_g < g_cost[n_idx]) {
        g_cost[n_idx] = new_g;
        parent[n_idx] = cur_idx;
        open.push({nx, ny, new_g, new_g + heuristic(nx, ny, gx, gy)});
      }
    }
  }

  return {};  // No path found
}

}  // namespace open_mower_next::coverage_planner