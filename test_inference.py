import tensorflow as tf
from filevideostream import FileVideoStream
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from vamos_plus_functions import box_overlap

saved_model_path = "files/tensorflow/saved_model"

print("Loading the Tensorflow model...", end=" ")
detect_fn = tf.saved_model.load(saved_model_path)
print("Done")

video = FileVideoStream(path="/mnt/ssd/Video-Cache/Jugend forscht/V-0030.MP4", start_frame=13).start()
image_np = video.read()

image_cropped = image_np[540:1620, 960:2880]

image = Image.fromarray(image_cropped)

draw = ImageDraw.Draw(image)

input_tensor = tf.convert_to_tensor(image_cropped)

input_tensor = input_tensor[tf.newaxis, ...]

detections = detect_fn(input_tensor)

num_detections = int(detections.pop("num_detections"))
detections = {key: value[0, :num_detections].numpy()
              for key, value in detections.items()}
detections["num_detections"] = num_detections

detections["detection_classes"] = detections["detection_classes"].astype(np.int64)

print(detections)
print(detections.keys())


def getCleanedUpBoxes(detection_list):
    boxes = detection_list["detection_boxes"]
    boxes_new = boxes
    replacing_list = []

    if len(boxes) <= 1:
        return boxes

    overlapping_boxes = []
    boxes_copy = boxes.copy()
    for i, box_pts in enumerate(boxes):
        boxes_copy.remove(box_pts)
        for i2, second_box_pts in enumerate(boxes_copy):
            if box_overlap(box_pts, second_box_pts, (3840, 2160), padding=5):
                extending_success = False
                for box_index, existing_overlapping_boxes in enumerate(overlapping_boxes):
                    if i in existing_overlapping_boxes or boxes.index(second_box_pts) in existing_overlapping_boxes:
                        overlapping_boxes[box_index].extend([i, boxes.index(second_box_pts)])
                        extending_success = True
                        break
                if not extending_success:
                    overlapping_boxes.append([i, boxes.index(second_box_pts)])

    overlapping_boxes = [sorted(list(set(x))) for x in overlapping_boxes]

    if len(overlapping_boxes) == 0:
        replacing_list.append([])
        return boxes
    for separate_box in overlapping_boxes:
        x_values = []
        y_values = []
        for index in separate_box:
            x_values.extend([boxes[index][1], boxes[index][3]])
            y_values.extend([boxes[index][0], boxes[index][2]])
        new_coordinates = [min(y_values), min(x_values), max(y_values), max(x_values)]

        replacing_scores = [detection_list["detection_scores"][x] for x in separate_box]
        replacing_list.append([replacing_scores, [max(replacing_scores), new_coordinates]])

    print(replacing_list)

    for i, item in enumerate(replacing_list):
        print("ITEM:", item)
        if len(item) == 0:
            continue
        for boxes_to_replace in item:
            print("BOXES TO REPLACE:", boxes_to_replace)
            for detection_score in range(len(boxes_to_replace)):
                print("DETECTION SCORE:", detection_score)
                del boxes_new[i][detection_score]
            boxes_new[i][boxes_to_replace[1][0]] = boxes_to_replace[1][1]

    return boxes_new


for index, score in enumerate(detections["detection_scores"]):
    if score < 0.01:
        continue

    box = detections["detection_boxes"][index]
    print(box)
    box = [
        box[1] * 3840,
        box[0] * 2160,
        box[3] * 3840,
        box[2] * 2160,
    ]

    draw.rectangle(box, outline=(3, 196, 255))

    left, top, right, bottom = draw.textbbox((box[0] + 5, box[1] - 33), f"Meteor: {score * 100:.2f}%", font=ImageFont.truetype("arial.ttf", 30))
    draw.rectangle((left-5, top-5, right+5, bottom+5), fill=(3, 196, 255))
    draw.text((box[0], box[1] - 34), f"Meteor: {score * 100:.2f}%", fill="black", font=ImageFont.truetype("arial.ttf", 30))

image.show()
