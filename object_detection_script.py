#object_detection_script

import collections
import json
import tarfile
import time
from pathlib import Path
from distutils.util import strtobool
import videoplayer as utils

import cv2
import numpy as np
from IPython import display
import openvino as ov
from openvino.tools.mo.front import tf as ov_tf_front
from openvino.tools import mo
import argparse

parser = argparse.ArgumentParser(description="OpenVino Object Detection")

#Add the Arguments
parser.add_argument('--model',default='ssdlite_mobilenet_v2', type=str, help='The model name')
parser.add_argument('--precision',default='FP16', type=str, help='Precision of model')
parser.add_argument('--device_name',default='CPU', type=str, help='Device Name for CPU or GPUs')
parser.add_argument('--threshold',default=.6, type=float, help='Keep box if above this threshold')
parser.add_argument('--fps',default=30, type=int, help='Frames per second')
parser.add_argument('--popup',default=False, type=lambda x: bool(strtobool(x)), help='OpenCV Video window enable or disable')
parser.add_argument('--output',default="data_file.json", type=str, help='File name for json output on data file')
parser.add_argument('--source',default='0', help='Device ID or RTSP IP Address')

args=parser.parse_args()

try:
    args.source = int(args.source)
except ValueError:
    pass

precision = args.precision
model_name = args.model
predict_pipeline = []

# The output path for the conversion.
converted_model_path = Path("model") / f"{model_name}_{precision.lower()}.xml"
core = ov.Core()

# Read the network and corresponding weights from a file.
model = core.read_model(model=converted_model_path)

# Compile the model for CPU (you can choose manually CPU, GPU etc.)
compiled_model = core.compile_model(model=model, device_name=args.device_name)

# Get the input and output nodes.
input_layer = compiled_model.input(0)
output_layer = compiled_model.output(0)

# Get the input size.
height, width = list(input_layer.shape)[1:3]
input_layer.any_name, output_layer.any_name

# https://tech.amikelive.com/node-718/what-object-categories-labels-are-in-coco-dataset/
classes = [
    "background", "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
    "truck", "boat", "traffic light", "fire hydrant", "street sign", "stop sign",
    "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant",
    "bear", "zebra", "giraffe", "hat", "backpack", "umbrella", "shoe", "eye glasses",
    "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite",
    "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
    "plate", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "mirror", "dining table", "window", "desk", "toilet",
    "door", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
    "toaster", "sink", "refrigerator", "blender", "book", "clock", "vase", "scissors",
    "teddy bear", "hair drier", "toothbrush", "hair brush"
]
# Colors for the classes above (Rainbow Color Map).
colors = cv2.applyColorMap(
    src=np.arange(0, 255, 255 / len(classes), dtype=np.float32).astype(np.uint8),
    colormap=cv2.COLORMAP_RAINBOW,
).squeeze()

def process_results(frame, results, thresh=args.threshold):
    # The size of the original frame.
    h, w = frame.shape[:2]
    # The 'results' variable is a [1, 1, 100, 7] tensor.
    results = results.squeeze()
    boxes = []
    labels = []
    scores = []
    for _, label, score, xmin, ymin, xmax, ymax in results:
        # Create a box with pixels coordinates from the box with normalized coordinates [0,1].
        boxes.append(
            tuple(map(int, (xmin * w, ymin * h, (xmax - xmin) * w, (ymax - ymin) * h)))
        )
        labels.append(int(label))
        scores.append(float(score))

    # Apply non-maximum suppression to get rid of many overlapping entities.
    # See https://paperswithcode.com/method/non-maximum-suppression
    # This algorithm returns indices of objects to keep.
    indices = cv2.dnn.NMSBoxes(
        bboxes=boxes, scores=scores, score_threshold=thresh, nms_threshold=thresh
    )

    # If there are no boxes.
    if len(indices) == 0:
        return []

    # Filter detected objects.
    return [(labels[idx], scores[idx], boxes[idx]) for idx in indices.flatten()]

def draw_boxes(frame, boxes):
    for label, score, box in boxes:
        # Choose color for the label.
        color = tuple(map(int, colors[label]))
        # Draw a box.
        x2 = box[0] + box[2]
        y2 = box[1] + box[3]
        cv2.rectangle(img=frame, pt1=box[:2], pt2=(x2, y2), color=color, thickness=3)

        # Draw a label name inside the box.
        cv2.putText(
            img=frame,
            text=f"{classes[label]} {score:.2f}",
            org=(box[0] + 10, box[1] + 30),
            fontFace=cv2.FONT_HERSHEY_COMPLEX,
            fontScale=frame.shape[1] / 1000,
            color=color,
            thickness=1,
            lineType=cv2.LINE_AA,
            )
    
    return frame

# Main processing function to run object detection.
def run_object_detection(source=args.source, flip=False, use_popup=args.popup, skip_first_frames=0):
    counter = 0
    player = None
    try:
        # Create a video player to play with target fps.
        player = utils.VideoPlayer(
            source=args.source, flip=flip, fps=args.fps, skip_first_frames=skip_first_frames
        )
        # Start capturing.
        player.start()
        if use_popup:
            title = "Press ESC to Exit"
            cv2.namedWindow(
                winname=title, flags=cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_AUTOSIZE
            )

        processing_times = collections.deque()
        while True:
            # Grab the frame.
            frame = player.next()
            if frame is None:
                print("Source ended")
                break
            # If the frame is larger than full HD, reduce size to improve the performance.
            scale = 1280 / max(frame.shape)
            if scale < 1:
                frame = cv2.resize(
                    src=frame,
                    dsize=None,
                    fx=scale,
                    fy=scale,
                    interpolation=cv2.INTER_AREA,
                )

            # Resize the image and change dims to fit neural network input.
            input_img = cv2.resize(
                src=frame, dsize=(width, height), interpolation=cv2.INTER_AREA
            )
            # Create a batch of images (size = 1).
            input_img = input_img[np.newaxis, ...]

            # Measure processing time
            start_time = time.time()
            # Get the results.
            results = compiled_model([input_img])[output_layer]
            stop_time = time.time()
            # Get poses from network results.
            boxes = process_results(frame=frame, results=results)
            for item in boxes:
                temp_dict = {}
                temp_dict['Frame'] = counter
                temp_dict['Time'] = start_time
                temp_dict['Label'] = item[0]
                temp_dict['Score'] = item[1]
                temp_dict['Label_text'] = classes[item[0]]
                temp_dict['Box'] = {'Xmin': item[2][0], 'Ymin': item[2][1], 'Xmax': item[2][2], 'Ymax': item[2][3]}
                predict_pipeline.append(temp_dict)
                counter += 1
            
            with open(args.output, "w+") as write_file:
                json.dump(predict_pipeline, write_file, indent = 4)

            # Draw boxes on a frame.
            filename = f'frame_{counter}.jpg'
            frame = draw_boxes(frame=frame, boxes=boxes)
            cv2.imwrite(filename,frame)

            processing_times.append(stop_time - start_time)
            # Use processing times from last 200 frames.
            if len(processing_times) > 200:
                processing_times.popleft()

            _, f_width = frame.shape[:2]
            # Mean processing time [ms].
            processing_time = np.mean(processing_times) * 1000
            fps = 1000 / processing_time
            cv2.putText(
                img=frame,
                text=f"Inference time: {processing_time:.1f}ms ({fps:.1f} FPS)",
                org=(20, 40),
                fontFace=cv2.FONT_HERSHEY_COMPLEX,
                fontScale=f_width / 1000,
                color=(0, 0, 255),
                thickness=1,
                lineType=cv2.LINE_AA,
            )

            # Use this workaround if there is flickering.
            if use_popup:
                cv2.imshow(winname=title, mat=frame)
                key = cv2.waitKey(1)
                # escape = 27
                if key == 27:
                    break
            else:
                # Encode numpy array to jpg.
                _, encoded_img = cv2.imencode(
                    ext=".jpg", img=frame, params=[cv2.IMWRITE_JPEG_QUALITY, 100]
                )
                # Create an IPython image.
                i = display.Image(data=encoded_img)
                # Display the image in this notebook.
                display.clear_output(wait=True)
                display.display(i)
         
    # ctrl-c
    except KeyboardInterrupt:
        print("Interrupted")
    # any different error
    except RuntimeError as e:
        print(e)
    finally:
        if player is not None:
            # Stop capturing.
            player.stop()
        if use_popup:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    run_object_detection(source=args.source, flip=isinstance(0, int), use_popup=args.popup)