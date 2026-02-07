from ultralytics import YOLO

# Load your model
model = YOLO('../models/arch2025.pt') # Change to your .pt file path

# Export the model
model.export(
    format='onnx',
    opset=12,          
    simplify=True,     # Fixes graph for OpenCV DNN
    imgsz=640          # Fixed input size
)