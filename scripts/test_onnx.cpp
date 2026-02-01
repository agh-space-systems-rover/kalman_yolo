#include <opencv2/opencv.hpp>
#include <opencv2/dnn.hpp>
#include <iostream>
#include <vector>
#include <string>

using namespace cv;
using namespace cv::dnn;
using namespace std;

// Constants for YOLO
const float INPUT_WIDTH = 640.0;
const float INPUT_HEIGHT = 640.0;
const float SCORE_THRESHOLD = 0.25;
const float NMS_THRESHOLD = 0.45;
const float CONFIDENCE_THRESHOLD = 0.25;

int main(int argc, char** argv) {
    if (argc < 3) {
        cerr << "Usage: " << argv[0] << " <model_path> <image_path>" << endl;
        return -1;
    }

    string modelPath = argv[1];
    string imagePath = argv[2];

    cout << "Loading model from: " << modelPath << endl;
    Net net;
    try {
        net = readNet(modelPath);
    } catch (const cv::Exception& e) {
        cerr << "Error loading model: " << e.what() << endl;
        return -1;
    }

    // Use CUDA if available
#ifdef CV_CUDA
    net.setPreferableBackend(DNN_BACKEND_CUDA);
    net.setPreferableTarget(DNN_TARGET_CUDA);
    cout << "Using CUDA backend" << endl;
#else
    net.setPreferableBackend(DNN_BACKEND_OPENCV);
    net.setPreferableTarget(DNN_TARGET_CPU);
    cout << "Using CPU backend" << endl;
#endif

    cout << "Loading image from: " << imagePath << endl;
    Mat image = imread(imagePath);
    if (image.empty()) {
        cerr << "Failed to load image" << endl;
        return -1;
    }

    // Preprocess image
    Mat blob;
    Size inputSize((int)INPUT_WIDTH, (int)INPUT_HEIGHT);
    blobFromImage(image, blob, 1./255., inputSize, Scalar(), true, false);
    
    net.setInput(blob);

    // Get output names
    vector<String> outNames = net.getUnconnectedOutLayersNames();
    cout << "Model output layers: ";
    for(const auto& name : outNames) cout << name << " ";
    cout << endl;

    // Forward pass
    cout << "Running inference..." << endl;
    vector<Mat> outputs;
    try {
        net.forward(outputs, outNames);
    } catch (const cv::Exception& e) {
        cerr << "\nOpenCV Exception during forward pass: " << e.what() << endl;
        cerr << "This might be due to a mismatch between the ONNX model opset and this OpenCV version." << endl;
        return -1;
    }

    if (outputs.empty()) {
        cerr << "No output from network." << endl;
        return -1;
    }

    // Post-process
    Mat prediction = outputs[0];
    
    // Normalize Shape
    if (prediction.dims == 3 && prediction.size[0] == 1) {
        // [1, Channels, Anchors] -> [Channels, Anchors]
        Mat view(prediction.size[1], prediction.size[2], CV_32F, prediction.data);
        transpose(view, prediction); // -> [Anchors, Channels]
    } else if (prediction.dims == 2 && prediction.rows < prediction.cols) {
         transpose(prediction, prediction);
    }
    
    int num_anchors = prediction.rows;
    int num_channels = prediction.cols;
    int num_classes = num_channels - 4;

    vector<int> class_ids;
    vector<float> confidences;
    vector<Rect> boxes;

    float x_factor = image.cols / INPUT_WIDTH;
    float y_factor = image.rows / INPUT_HEIGHT;

    float* data = (float*)prediction.data;

    for (int i = 0; i < num_anchors; i++) {
        float* row_ptr = prediction.ptr<float>(i);
        float* classes_scores = row_ptr + 4;
        
        Point class_id_point;
        double max_class_score;
        minMaxLoc(Mat(1, num_classes, CV_32F, classes_scores), 0, &max_class_score, 0, &class_id_point);

        if (max_class_score > SCORE_THRESHOLD) {
            float cx = row_ptr[0];
            float cy = row_ptr[1];
            float w = row_ptr[2];
            float h = row_ptr[3];

            int left = int((cx - 0.5 * w) * x_factor);
            int top = int((cy - 0.5 * h) * y_factor);
            int width = int(w * x_factor);
            int height = int(h * y_factor);

            boxes.push_back(Rect(left, top, width, height));
            confidences.push_back(max_class_score);
            class_ids.push_back(class_id_point.x);
        }
    }

    vector<int> nms_result;
    NMSBoxes(boxes, confidences, SCORE_THRESHOLD, NMS_THRESHOLD, nms_result);

    cout << "Found " << nms_result.size() << " detections" << endl;

    for (int idx : nms_result) {
        Rect box = boxes[idx];
        rectangle(image, box, Scalar(0, 255, 0), 2);
        
        string label = format("Class %d: %.2f", class_ids[idx], confidences[idx]);
        putText(image, label, Point(box.x, box.y - 5), FONT_HERSHEY_SIMPLEX, 0.5, Scalar(0, 255, 0), 1);
    }

    imwrite("result_cpp.jpg", image);
    cout << "Saved result to result_cpp.jpg" << endl;

    if (image.cols > 1200) {
        float r = 1200.0f / image.cols;
        resize(image, image, Size(), r, r);
    }

    try {
        namedWindow("Detections", WINDOW_AUTOSIZE);
        imshow("Detections", image);
        cout << "Press any key to close the window..." << endl;
        waitKey(0);
    } catch (const cv::Exception& e) {
        cerr << "Warning: GUI not available or failed: " << e.what() << endl;
        cerr << "Check result_cpp.jpg instead." << endl;
    }

    return 0;
}
