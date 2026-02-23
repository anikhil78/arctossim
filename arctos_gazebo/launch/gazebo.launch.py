import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    ExecuteProcess,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_description = get_package_share_directory('arctos_description')
    pkg_gazebo = get_package_share_directory('arctos_gazebo')

    initial_positions_file = os.path.join(
        pkg_description, 'config', 'initial_positions.yaml'
    )
    controllers_file = os.path.join(
        pkg_gazebo, 'config', 'ros2_controllers.yaml'
    )
    world_file = os.path.join(pkg_gazebo, 'worlds', 'empty.world')
    xacro_file = os.path.join(pkg_description, 'urdf', 'arctos_sim.xacro')

    # Build robot description from xacro
    robot_description_content = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ',
            xacro_file, ' ',
            'initial_positions_file:=', initial_positions_file, ' ',
            'ros2_controllers_file:=', controllers_file,
        ]),
        value_type=str,
    )
    robot_description = {'robot_description': robot_description_content}

    # --- Nodes ---

    # 1. Gazebo (Classic)
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'), 'launch', 'gazebo.launch.py'
            ])
        ]),
        launch_arguments={
            'world': world_file,
            'verbose': 'true',
        }.items(),
    )

    # 2. Robot state publisher (publishes /robot_description and TF)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description],
    )

    # 3. Spawn robot entity in Gazebo from /robot_description topic
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-topic', 'robot_description', '-entity', 'arctos', '-timeout', '120'],
        output='screen',
    )

    # 4. Load joint_state_broadcaster after spawn completes
    load_joint_state_broadcaster = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller',
             '--set-state', 'active', 'joint_state_broadcaster'],
        output='screen',
    )

    # 5. Load arm trajectory controller after joint_state_broadcaster is active
    load_arm_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller',
             '--set-state', 'active', 'arctos_arm_controller'],
        output='screen',
    )

    # 6. Load gripper controller last
    load_hand_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller',
             '--set-state', 'active', 'arctos_hand_controller'],
        output='screen',
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity,

        # Sequential controller loading via event handlers
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[load_joint_state_broadcaster],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_joint_state_broadcaster,
                on_exit=[load_arm_controller],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_arm_controller,
                on_exit=[load_hand_controller],
            )
        ),
    ])
