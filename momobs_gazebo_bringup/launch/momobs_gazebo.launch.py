import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
import xacro
import re

def generate_launch_description():


    def remove_comments(text):
        pattern = r'<!--(.*?)-->'
        return re.sub(pattern, '', text, flags=re.DOTALL)

    force_arg = DeclareLaunchArgument('force', default_value='false', description='Launch extra nodes if true')
    residual_arg = DeclareLaunchArgument('residuals', default_value='false', description='Launch extra nodes if true')


    description_pkg = get_package_share_directory('anymal_c_simple_description')
    momobs_ros_pkg = get_package_share_directory('momobs_ros2')
    config_pkg_share = get_package_share_directory('anymal_c_config')


    description_launch_file = os.path.join(description_pkg, 'launch', 'floating_base_description.launch.py')   
    gazebo_description_launch_file = os.path.join(description_pkg, 'launch', 'gazebo_description.launch.py')   
    momobs_launch_file = os.path.join(momobs_ros_pkg, 'launch', 'gazebo_wrapper.launch.py')
    gazebo_config = os.path.join(config_pkg_share, 'config', 'gazebo.yaml')

    default_model_path = os.path.join(description_pkg, "urdf/anymal_main.xacro")
    xacro_content = xacro.process_file(default_model_path)

    momobs = IncludeLaunchDescription(PythonLaunchDescriptionSource(momobs_launch_file))
    description = IncludeLaunchDescription(PythonLaunchDescriptionSource(description_launch_file))
    gazebo_description = IncludeLaunchDescription(PythonLaunchDescriptionSource(gazebo_description_launch_file))


    joints_config = os.path.join(config_pkg_share, "config/joints/joints.yaml")
    gait_config = os.path.join(config_pkg_share, "config/gait/gait.yaml")
    links_config = os.path.join(config_pkg_share, "config/links/links.yaml")


    force_plotter = Node(
        package='momobs_plot',
        executable='force_plotter.py',
        condition=IfCondition(LaunchConfiguration('force')),
        emulate_tty=True,
        parameters=[{
            'autoscale':True,
            'listening':True
        }]
    )

    residual_plotter = Node(
        package='momobs_plot',
        executable='residual_plotter.py',
        condition=IfCondition(LaunchConfiguration('residuals')),
        parameters=[{
            'autoscale':True,
            'listening':True,
            'x_lim':3000
        }]
    )

    quadruped_controller_node = Node(
        package="champ_base",
        executable="quadruped_controller_node",
        output="screen",
        parameters=[
            {"use_sim_time": False},
            {"gazebo": True},
            {"publish_joint_states": False},
            {"publish_joint_control": True},
            {"publish_foot_contacts": True},
            {"joint_controller_topic": '/joint_group_position_controller/joint_trajectory'},
            {"loop_rate": 500.0},
            {"urdf": remove_comments(xacro_content.toxml())},
            {joints_config},
            {links_config},
            {gait_config}
        ],
        remappings=[("/cmd_vel/smooth", "/cmd_vel")],
    )



    start_gazebo_server_cmd = ExecuteProcess(
        cmd=[
            "gzserver",
            # "--pause",
            "-s",
            "libgazebo_ros_init.so",
            "-s",
            "libgazebo_ros_factory.so",
            # '--ros-args',
            # '--params-file',
            # gazebo_config
        ],
        # cwd=[launch_dir],
        output="screen",
    )

    start_gazebo_client_cmd = ExecuteProcess(
        cmd=["gzclient"],
        # cwd=[launch_dir],
        output="screen",
    )

    timer = TimerAction(
            period=1.0,  # Delay time in seconds
            actions=[]   # No actions, just waiting
        )

    start_gazebo_spawner_cmd = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        output="screen",
        arguments=[
            "-entity",
            "ANYmal",
            "-topic",
            "/robot_description",
            # "-robot_namespace",
            # "",
            "-x",
            "0.0",
            "-y",
            "0.0",
            "-z",
            "0.6",
            "-R",
            "0",
            "-P",
            "0",
            "-Y",
            "0.0",
        ],
    )

    load_joint_trajectory_position_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_group_position_controller'],
        output='screen'
    )


    load_joint_state_broadcaster = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_state_broadcaster'],
        output='screen'
    )




    return LaunchDescription(
        [
            force_arg,
            residual_arg,
            description,
            momobs,
            force_plotter,
            residual_plotter,
            quadruped_controller_node,
            gazebo_description,
            start_gazebo_server_cmd,
            start_gazebo_client_cmd,
            timer,
            start_gazebo_spawner_cmd,
            load_joint_trajectory_position_controller,
            load_joint_state_broadcaster
        ]
    )