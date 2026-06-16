#!/usr/bin/env python3
"""
Batch simulation runner for overnight regression testing.

Boots the sim via docker compose, records a ros2 bag of key topics, waits
for /mowing_done, tears down, then moves to the next run.

Usage (from ~/OpenMowerWindows on the host):
    python3 tests/test_batch_runner.py
    python3 tests/test_batch_runner.py --runs run_001_center_field run_003_north_zone
    python3 tests/test_batch_runner.py --dry-run

Bags land in ~/OpenMowerWindows/bags/<run_name>_<timestamp>/

How it works:
  - /mowing_done (std_msgs/Bool) is published True by coverage_goal_bridge.py
    when Nav2 signals completion (success or failure).
  - The runner blocks on that topic per run, with a hard timeout as a fallback.
  - SIGINT (Ctrl-C) mid-run stops the current bag cleanly before aborting.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

# ── Project layout ─────────────────────────────────────────────────────────────
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMPOSE_FILE = os.path.join(PROJECT_DIR, "docker-compose.yaml")
CONTAINER = "openmowerwindows-workspace-1"
BAGS_HOST_DIR = os.path.join(PROJECT_DIR, "bags")
BAGS_CONTAINER_DIR = "/opt/ws/bags"

# Preamble injected before every docker exec command so ROS2 is on PATH.
_ROS_SOURCE = (
    "source /opt/ros/jazzy/setup.bash && "
    "source /opt/ws/install/setup.bash && "
    "export ROS_DOMAIN_ID=42 && "
)

# ── Topics captured in every bag ──────────────────────────────────────────────
BAG_TOPICS = [
    "/odometry/filtered/map",   # map-frame EKF output (ekf_se_map)
    "/cmd_vel",                 # twist_mux merged velocity
    "/scan",                    # radar LaserScan
    "/mowing_goal",             # trigger topic (what goal was sent)
    "/plan",                    # Nav2 planned path
    "/tf",
    "/tf_static",
    "/mowing_done",             # completion signal from coverage_goal_bridge
]

# ── Test run definitions ───────────────────────────────────────────────────────
# Add, remove, or reorder entries here to configure the overnight batch.
# goal_x / goal_y: map-frame coordinates of the mowing target (metres).
# timeout_sec:     hard cap per run; bag is saved even if mowing doesn't finish.
RUNS: list[dict] = [
    {
        "name": "run_001_center_field",
        "description": "Baseline — mow the centre of open_field.sdf",
        "goal_x": 0.0,
        "goal_y": 0.0,
        "timeout_sec": 900,
    },
    {
        "name": "run_002_east_zone",
        "description": "Mowing zone offset 5 m east — asymmetric approach path",
        "goal_x": 5.0,
        "goal_y": 0.0,
        "timeout_sec": 900,
    },
    {
        "name": "run_003_north_zone",
        "description": "Mowing zone offset 5 m north",
        "goal_x": 0.0,
        "goal_y": 5.0,
        "timeout_sec": 900,
    },
    {
        "name": "run_004_diagonal_corner",
        "description": "Corner approach — longer initial transit, tests planner stability",
        "goal_x": 6.0,
        "goal_y": 6.0,
        "timeout_sec": 1200,
    },
    {
        "name": "run_005_negative_quadrant",
        "description": "Negative-coordinate zone — west/south of world origin",
        "goal_x": -5.0,
        "goal_y": -5.0,
        "timeout_sec": 900,
    },
]


# ── Logging ───────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── Subprocess helpers ────────────────────────────────────────────────────────

def _host_run(cmd: list[str], check: bool = False, **kwargs) -> subprocess.CompletedProcess:
    log(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=PROJECT_DIR, check=check, **kwargs)


def _docker_exec(
    bash_cmd: str,
    *,
    background: bool = False,
    timeout: int | None = None,
) -> subprocess.CompletedProcess:
    flag = ["-d"] if background else []
    cmd = ["docker", "exec", *flag, CONTAINER, "bash", "-c", _ROS_SOURCE + bash_cmd]
    mode = "(bg)" if background else "    "
    log(f"  exec{mode}> {bash_cmd[:110]}")
    return subprocess.run(cmd, cwd=PROJECT_DIR, timeout=timeout)


# ── Sim lifecycle ─────────────────────────────────────────────────────────────

def start_sim() -> None:
    log("Starting sim (docker compose up -d)…")
    _host_run(["docker", "compose", "-f", COMPOSE_FILE, "up", "-d"], check=True)


def stop_sim() -> None:
    log("Stopping sim (docker compose down)…")
    _host_run(["docker", "compose", "-f", COMPOSE_FILE, "down"])


def wait_for_sim_ready(timeout_sec: int = 120) -> bool:
    """Poll until /mowing_goal appears in ros2 topic list — proxy for full stack up."""
    log(f"Waiting up to {timeout_sec}s for sim to be ready…")
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["docker", "exec", CONTAINER, "bash", "-c",
             _ROS_SOURCE + "ros2 topic list 2>/dev/null"],
            capture_output=True, text=True, cwd=PROJECT_DIR,
        )
        if "/mowing_goal" in result.stdout:
            log("Sim ready.")
            return True
        time.sleep(5)
    log("ERROR: sim did not become ready within the timeout.")
    return False


# ── Bag recording ─────────────────────────────────────────────────────────────

def start_bag_record(bag_container_path: str) -> None:
    topics = " ".join(BAG_TOPICS)
    _docker_exec(
        f"ros2 bag record -o {bag_container_path} {topics} >> /tmp/bag_record.log 2>&1",
        background=True,
    )
    time.sleep(2)  # let the recorder subscribe before the goal fires


def stop_bag_record() -> None:
    log("Stopping bag record (SIGINT to flush cleanly)…")
    subprocess.run(
        ["docker", "exec", CONTAINER, "bash", "-c",
         "pkill -2 -f 'ros2 bag record' || true"],
        cwd=PROJECT_DIR,
    )
    time.sleep(3)  # wait for the bag writer to flush and close


# ── Mowing goal ───────────────────────────────────────────────────────────────

def send_mowing_goal(x: float, y: float) -> None:
    pose = (
        f"{{header: {{frame_id: 'map'}}, "
        f"pose: {{position: {{x: {x}, y: {y}, z: 0.0}}, "
        f"orientation: {{w: 1.0}}}}}}"
    )
    _docker_exec(
        f"ros2 topic pub --once /mowing_goal geometry_msgs/msg/PoseStamped '{pose}'",
        timeout=30,
    )


def wait_for_mowing_done(timeout_sec: int) -> bool:
    """Block until /mowing_done fires True or timeout expires."""
    log(f"Waiting up to {timeout_sec}s for /mowing_done…")
    try:
        result = _docker_exec(
            "ros2 topic echo --once /mowing_done std_msgs/msg/Bool",
            timeout=timeout_sec,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log("Timed out waiting for /mowing_done — saving partial bag.")
        return False


# ── Single run orchestration ──────────────────────────────────────────────────

def execute_run(run: dict, dry_run: bool = False) -> bool:
    name = run["name"]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bag_name = f"{name}_{timestamp}"
    bag_container_path = f"{BAGS_CONTAINER_DIR}/{bag_name}"

    log(f"=== Run: {name} ===")
    log(f"    {run['description']}")
    log(f"    Goal: x={run['goal_x']}, y={run['goal_y']}  timeout={run['timeout_sec']}s")
    log(f"    Bag : {BAGS_HOST_DIR}/{bag_name}/")

    if dry_run:
        log("    [dry-run] skipping execution.")
        return True

    success = False
    try:
        start_sim()
        if not wait_for_sim_ready():
            log(f"FAIL: sim never became ready for {name}.")
            return False

        start_bag_record(bag_container_path)
        send_mowing_goal(run["goal_x"], run["goal_y"])
        success = wait_for_mowing_done(run["timeout_sec"])

        if success:
            log(f"Run {name}: DONE (mowing complete).")
        else:
            log(f"Run {name}: TIMEOUT (partial bag saved).")

    except KeyboardInterrupt:
        log("Run interrupted — flushing bag and re-raising.")
        raise

    finally:
        stop_bag_record()
        stop_sim()
        log("")

    return success


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Overnight batch mowing simulation runner.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 tests/test_batch_runner.py\n"
            "  python3 tests/test_batch_runner.py --runs run_001_center_field\n"
            "  python3 tests/test_batch_runner.py --dry-run\n"
        ),
    )
    parser.add_argument(
        "--runs", nargs="*", metavar="NAME",
        help="Run only these runs by name (default: all RUNS).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would run without starting Docker.",
    )
    args = parser.parse_args()

    selected = RUNS
    if args.runs:
        names = set(args.runs)
        selected = [r for r in RUNS if r["name"] in names]
        if not selected:
            unknown = names - {r["name"] for r in RUNS}
            print(f"ERROR: unknown run name(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            print("Available:", ", ".join(r["name"] for r in RUNS), file=sys.stderr)
            sys.exit(1)

    os.makedirs(BAGS_HOST_DIR, exist_ok=True)

    log(f"Batch runner starting — {len(selected)} run(s) queued.")
    if args.dry_run:
        log("[dry-run mode — no processes will be started]")

    passed = failed = 0

    try:
        for i, run in enumerate(selected, 1):
            log(f"--- [{i}/{len(selected)}] ---")
            try:
                ok = execute_run(run, dry_run=args.dry_run)
                if ok:
                    passed += 1
                else:
                    failed += 1
            except KeyboardInterrupt:
                log("Batch aborted by user.")
                failed += 1
                break
            except Exception as exc:
                log(f"ERROR in run {run['name']}: {exc}")
                failed += 1
                # Best-effort cleanup before moving to next run.
                try:
                    stop_bag_record()
                    stop_sim()
                except Exception:
                    pass

    finally:
        log(f"=== Batch complete: {passed} passed, {failed} failed ===")
        log(f"Bags saved to: {BAGS_HOST_DIR}/")


if __name__ == "__main__":
    main()