colcon build --packages-skip haptiquad_ros2 
source install/setup.bash
colcon build --packages-select haptiquad_ros2 --cmake-force-configure