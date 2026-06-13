from ament_index_python import get_package_share_path
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.descriptions import ParameterFile

def find_configs() -> set[str]:
    config_path = get_package_share_path("kalman_yolo") / "config"
    return {x.stem for x in config_path.glob("*.yaml")}


def launch_setup(context):
    # Retrieve the raw space-separated string of camera IDs
    rgbd_ids_str = LaunchConfiguration("rgbd_ids").perform(context)
    
    rgbd_ids = [
        x
        for x in rgbd_ids_str.split(" ")
        if x != ""
    ]
    config = LaunchConfiguration("config").perform(context)

    # Base parameters loaded from the specified YAML configuration file
    parameters = [
        ParameterFile(
            str(get_package_share_path("kalman_yolo") / "config" / f"{config}.yaml"),
            allow_substs=True,
        ),
        {"num_cameras": len(rgbd_ids)},
    ]
    
    remappings = sum(
        [
            [
                (f"color{i}", f"{rgbd_id}/color/image_raw"),
                (f"color{i}/compressed", f"{rgbd_id}/color/image_raw/compressed"),
                (f"depth{i}", f"{rgbd_id}/depth/image_raw"),
                (
                    f"depth{i}/compressed",
                    f"{rgbd_id}/depth/image_raw/compressed",
                ),
                (f"info{i}", f"{rgbd_id}/color/camera_info"),
                (f"detections", f"yolo_detections"),
                (f"annotated{i}", f"{rgbd_id}/yolo_annotated"),
                (f"annotated{i}/compressed", f"{rgbd_id}/yolo_annotated/compressed"),
            ]
            for i, rgbd_id in enumerate(rgbd_ids)
        ],
        [],
    )

    max_distance = float(LaunchConfiguration("max_distance").perform(context))

    return [
        Node(
            package="yolo_ros",
            executable="yolo_detect_auto_activate",
            parameters=parameters,
            remappings=remappings,
        ),
        Node(
            package="kalman_arc",
            executable="darkest_boulder",
            name="darkest_boulder_filter",
            parameters=[
                {
                    "rgbd_ids": rgbd_ids_str,
                    "max_distance": max_distance,
                }
            ],
            output="screen",
        ),
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "rgbd_ids",
                default_value="",
                description="Space-separated IDs of the depth cameras to use.",
            ),
            DeclareLaunchArgument(
                "config",
                choices=find_configs(),
                description="name of the configuration to load",
            ),
            DeclareLaunchArgument(
                "max_distance",
                default_value="5.0",
                description="Maximum boulder distance in meters (global_frame).",
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )