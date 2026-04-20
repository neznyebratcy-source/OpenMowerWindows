###
# coverage_planner_plugin  —  Nav2 GlobalPlanner plugin
#
# Provides boustrophedon coverage path planning with A* obstacle avoidance.
# Loaded by pluginlib at runtime; not a standalone executable.
###

find_package(nav2_core      REQUIRED)
find_package(nav2_costmap_2d REQUIRED)
find_package(nav2_util      REQUIRED)

add_library(coverage_planner_plugin SHARED
    src/coverage_planner/coverage_planner.cpp
)

target_compile_features(coverage_planner_plugin PUBLIC cxx_std_17)

target_include_directories(coverage_planner_plugin PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(coverage_planner_plugin
    rclcpp
    rclcpp_lifecycle
    nav2_core
    nav2_costmap_2d
    nav2_util
    nav_msgs
    geometry_msgs
    tf2
    tf2_ros
    tf2_geometry_msgs
    pluginlib
)

# Link against the generated message typesupport so we can use
# open_mower_next::msg::Map / Area
target_link_libraries(coverage_planner_plugin
    "${cpp_typesupport_target}"
)

# Register the plugin description file with pluginlib so it is found at runtime
pluginlib_export_plugin_description_file(nav2_core src/coverage_planner/plugins.xml)

# Ensure message typesupport is generated before compiling the plugin
add_dependencies(coverage_planner_plugin ${PROJECT_NAME})

install(TARGETS coverage_planner_plugin
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)