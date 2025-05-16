""" import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command
from launch.event_handlers import OnProcessStart

def generate_launch_description():
    package_name = 'bot_pkg1'

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'rsp.launch.py')
        ]),
        launch_arguments={'use_sim_time': 'false'}.items()
    )

    controller_param_file = os.path.join(
        get_package_share_directory(package_name), 'config', 'my_controllers.yaml')

    robot_description = Command(
        ['ros2 param get --hide-type /robot_state_publisher robot_description'])

    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        arguments=['diff_cont'],
        parameters=[{'robot_description': robot_description},
                    controller_param_file]
    )

    delayed_controller_manager = TimerAction(
        period=3.0,
        actions=[controller_manager]
    )

    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner.py',
        arguments=['diff_cont'],
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        OnProcessStart(
            target_action=controller_manager,
            on_start=[diff_drive_spawner]
        )
    )

    joint_broad_spawner = Node(
        package='controller_manager',
        executable='spawner.py',
        arguments=['joint_broad'],
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        OnProcessStart(
            target_action=controller_manager,
            on_start=[joint_broad_spawner]
        )
    )

    return LaunchDescription([
        rsp,
        delayed_controller_manager,
        delayed_diff_drive_spawner,
        delayed_joint_broad_spawner
    ])
 """

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue
from launch.event_handlers import OnProcessStart, OnProcessExit

def generate_launch_description():
    pkg = 'bot_pkg1'
    share = get_package_share_directory(pkg)

    # 1) rsp (robot_state_publisher) ------------------------------------------------
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(share, 'launch', 'rsp.launch.py')),
        launch_arguments={'use_sim_time': 'false'}.items()
    )

    # 2) controllers YAML ----------------------------------------------------------
    controller_param_file = os.path.join(share, 'config', 'my_controllers.yaml')

    # 3) grab the URDF off of /robot_state_publisher --------------------------------
    robot_description = Command([
        'ros2 param get --hide-type /robot_state_publisher robot_description'
    ])

    # 4) controller_manager (ros2_control_node) ------------------------------------
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        namespace='controller_manager',    # <— important so the service is /controller_manager/...
        parameters=[
          # wrap URDF in a ParameterValue as a STR so it's not YAML-parsed
          {'robot_description':
             ParameterValue(robot_description, value_type=str)},
          controller_param_file
        ],
        output='screen',
    )

    # 5) delay 3s just in case, then start the control node ------------------------
    delayed_controller_manager = TimerAction(
        period=3.0,
        actions=[controller_manager]
    )

    # 6) spawners bound to events -----------------------------------------------
    diff_drive_spawner = Node(
        package='controller_manager', executable='spawner.py',
        arguments=['diff_cont'],
    )
    joint_broad_spawner = Node(
        package='controller_manager', executable='spawner.py',
        arguments=['joint_broad'],
    )

    # a) spawn diff_cont as soon as controller_manager starts
    delayed_diff_drive_spawner = RegisterEventHandler(
        OnProcessStart(
            target_action=controller_manager,
            on_start=[diff_drive_spawner]
        )
    )
    # b) spawn joint_broad once controller_manager has fully come up
    delayed_joint_broad_spawner = RegisterEventHandler(
        OnProcessExit(
            target_action=controller_manager,
            on_exit=[joint_broad_spawner]
        )
    )

    return LaunchDescription([
        rsp,
        delayed_controller_manager,
        delayed_diff_drive_spawner,
        delayed_joint_broad_spawner,
    ])
