from ultralytics import YOLO
import sys
import cv2

def test_yolo_onnx(model_path, image_path):
    print(f"Loading ONNX model via Ultralytics: {model_path}")
    
    # Load the exported ONNX model
    # The YOLO class automatically handles loading ONNX models via onnxruntime
    model = YOLO(model_path, task='detect')
    
    print(f"Running inference on: {image_path}")
    # Run inference
    results = model(image_path)
    
    # Results is a list of Result objects
    for result in results:
        print(f"Detected {len(result.boxes)} objects.")
        
        # Save the plotted image
        output_path = "result_ort.jpg"
        result.save(filename=output_path)
        print(f"Result saved to {output_path}")
        
        # Open in window
        img = cv2.imread(output_path)
        if img is not None:
             # Resize for display if too large (e.g. width > 1200 pixels)
            if img.shape[1] > 1200:
                scale = 1200.0 / img.shape[1]
                img = cv2.resize(img, (0,0), fx=scale, fy=scale)
                
            cv2.imshow("Detection (ONNX Runtime)", img)
            print("Press any key to close the window...")
            cv2.waitKey(0)
            cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 test_onnx_ort.py <model.onnx> <image.png>")
    else:
        test_yolo_onnx(sys.argv[1], sys.argv[2])
