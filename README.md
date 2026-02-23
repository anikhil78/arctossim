# arctossim

Gazebo Classic simulation of the Arctos 6-DOF robotic arm with `ros2_control`.

## Prerequisites

- Ubuntu 22.04
- ROS 2 Humble ([install guide](https://docs.ros.org/en/humble/Installation.html))

Install required ROS packages:

```bash
sudo apt update
sudo apt install -y \
  ros-humble-gazebo-ros-pkgs \
  ros-humble-gazebo-ros2-control \
  ros-humble-ros2-controllers \
  ros-humble-robot-state-publisher \
  ros-humble-xacro
```

## Setup

```bash
# 1. Create a fresh workspace
mkdir -p ~/arctos_ws/src
cd ~/arctos_ws/src

# 2. Clone this repo
git clone https://github.com/anikhil78/arctossim.git

# 3. Install any remaining dependencies via rosdep
cd ~/arctos_ws
rosdep install --from-paths src --ignore-src -r -y

# 4. Build
colcon build --packages-select arctos_description arctos_gazebo

# 5. Source the workspace
source install/setup.bash
```

## Launch

```bash
ros2 launch arctos_gazebo gazebo.launch.py
```

This starts:
1. Gazebo Classic with an empty world
2. `robot_state_publisher` (publishes URDF + TF)
3. The Arctos arm spawned in Gazebo
4. `joint_state_broadcaster`, `arctos_arm_controller`, `arctos_hand_controller`

## Package structure

```
arctossim/
├── arctos_description/       # Robot model
│   ├── urdf/
│   │   ├── arctos.xacro              # 6-DOF arm kinematics
│   │   ├── arctos_gripper.xacro      # Parallel jaw gripper
│   │   ├── arctos.ros2_control.xacro # Hardware interface (Gazebo plugin)
│   │   ├── arctos_sim.xacro          # Top-level entry point
│   │   └── common/                   # Shared macros and materials
│   ├── meshes/                       # STL files for all links
│   └── config/
│       └── initial_positions.yaml    # All joints start at 0
│
└── arctos_gazebo/            # Simulation launch
    ├── launch/
    │   └── gazebo.launch.py          # Main launch file
    ├── config/
    │   └── ros2_controllers.yaml     # Controller definitions
    └── worlds/
        └── empty.world               # Ground plane + sun
```

## Sending commands

Once running, send a goal to the arm controller:

```bash
ros2 action send_goal /arctos_arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [X_joint, Y_joint, Z_joint, A_joint, B_joint, C_joint],
    points: [{positions: [0.5, 0.3, 0.2, 0.0, 0.0, 0.0], time_from_start: {sec: 2}}]}}"
```

## Adding MoveIt (next step)

The setup is structured so MoveIt can be added with a new `arctos_moveit_config` package:
- The `JointTrajectoryController` already provides the `FollowJointTrajectory` action that MoveIt expects
- The SRDF from the reference hardware repo can be reused directly
- Add a `moveit.launch.py` that includes `gazebo.launch.py` and starts `move_group`
