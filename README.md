# Kalman YOLO

Model weights and configs for [yolo_ros](https://github.com/agh-space-systems-rover/kalman_robot/tree/main/yolo_ros). Detection and segmentation YOLO models are supported.

## Repository Structure

- `config`: Configuration files for different competitions.
- `models`: Pre-trained YOLO models in PyTorch `.pt` format.
- `launch`: A launch file for this package. Accepts arguments:
    - `rgbd_ids=(space separated camera names, e.g. d455_front)`
    - `config=(name of config file without .yaml suffix)`

## Adding a new Model

Use [`yolo-gym`](https://github.com/agh-space-systems-rover/yolo-gym) to train a detection or segmentation model and copy the PyTorch weights over here to the `models` directory. Then create a new config file in the `config` directory. Remember to update the parameters, in particular: `model`, `class_names`, `class_radii`. For segmentation models, instance masks are used internally for depth/size estimation when available; Humble `vision_msgs/Detection2D` does not publish masks in `/detections`.
