from ament_index_python import get_package_share_path
from launch import LaunchDescription
from launch_ros.actions import Node, LoadComposableNodes
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.descriptions import ComposableNode, ParameterFile


def launch_setup(context):
    rgbd_ids = [
        x
        for x in LaunchConfiguration("rgbd_ids").perform(context).split(" ")
        if x != ""
    ]
    config = LaunchConfiguration("config").perform(context)

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
                (f"depth{i}", f"{rgbd_id}/aligned_depth_to_color/image_raw"),
                (
                    f"depth{i}/compressed",
                    f"{rgbd_id}/aligned_depth_to_color/image_raw/compressed",
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

    return [
        Node(
            package="yolo_ros",
            executable="yolo_detect_auto_activate",
            parameters=parameters,
            remappings=remappings,
        )
    ]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "rgbd_ids",
                description="Space-separated IDs of the depth cameras to use.",
                default_value="",
            ),
            DeclareLaunchArgument(
                "config",
                description="name of the configuration to load",
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
