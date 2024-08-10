import datetime
import json
import math
import os
import shutil
import statistics
import time
from datetime import timedelta
from xml.dom import minidom

# os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import cv2
import numpy
import numpy as np
import tensorflow as tf
from PyQt5.QtCore import QTime, Qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QProgressDialog

from filevideostream import FileVideoStream


def check_pos(first, second, thresh):
    f_x, f_y = first
    s_x, s_y = second
    if abs(f_x - s_x) <= thresh and abs(f_y - s_y) <= thresh:
        return True
    else:
        return False


def distance(a, b):
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)


def calculate_area(pts):
    y1, x1, y2, x2 = pts
    return abs(y1 - y2) * abs(x1 - x2)


def box_overlap(box1, box2, resolution, padding=0):
    """Incoming format is y1, x1, y2, x2.
    Padding is optional, but can improve post-processing.
    """
    box1_ymin, box1_xmin, box1_ymax, box1_xmax = box1
    box2_ymin, box2_xmin, box2_ymax, box2_xmax = box2
    if box1_ymin == resolution[1]:
        box1_ymin -= padding
    elif box2_ymin == resolution[1]:
        box2_ymin -= padding
    elif box1_ymax == resolution[1]:
        box1_ymax -= padding
    elif box2_ymax == resolution[1]:
        box2_ymax -= padding
    elif box1_xmin == resolution[0]:
        box1_xmin -= padding
    elif box2_xmin == resolution[0]:
        box2_xmin -= padding
    elif box1_xmax == resolution[0]:
        box1_xmax -= padding
    elif box2_xmax == resolution[0]:
        box2_xmax -= padding
    if box1_ymin == 0:
        box1_ymin += padding
    elif box2_ymin == 0:
        box2_ymin += padding
    elif box1_ymax == 0:
        box1_ymax += padding
    elif box2_ymax == 0:
        box2_ymax += padding
    elif box1_xmin == 0:
        box1_xmin += padding
    elif box2_xmin == 0:
        box2_xmin += padding
    elif box1_xmax == 0:
        box1_xmax += padding
    elif box2_xmax == 0:
        box2_xmax += padding
    return not (
            box1_xmax + padding < box2_xmin - padding or
            box1_xmin - padding > box2_xmax + padding or
            box1_ymax + padding < box2_ymin - padding or
            box1_ymin - padding > box2_ymax + padding
    )


def analyse_detections_list(videopath, xmlpath, folderpath, video_id, window, use_xml):
    with open(os.path.join(folderpath, "detections_list_" + video_id + ".txt"), "r") as f:
        meteor_data = json.loads(f.read())

    if use_xml:
        # Reading and processing the XML-file
        try:
            xml_file = minidom.parse(xmlpath)
        except FileNotFoundError:
            xml_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected XML file does not exist.")
            xml_not_found.setWindowTitle("XML not found")
            xml_not_found.exec_()
            return False, {}, []
        try:
            creation_date = xml_file.getElementsByTagName('CreationDate')
            creation_date = creation_date[0].attributes['value'].value

            year, month, day, hour, minute, second = int(creation_date[:4]), int(creation_date[5:7]), int(
                creation_date[8:10]), int(creation_date[11:13]), int(creation_date[14:16]), int(creation_date[17:19])
        except IndexError:
            xml_not_valid = QMessageBox(icon=QMessageBox.Critical,
                                        text='The selected XML file is not valid, the key "creationDate" and its '
                                             'value is missing.')
            xml_not_valid.setWindowTitle("XML not valid")
            xml_not_valid.exec_()
            return False, {}, []

        base_time = datetime.datetime(year, month, day, hour, minute, second)
    else:
        base_time = window.base_time

    return True, meteor_data, [], convert_datetime(base_time)


def analyse(videopath, xmlpath, folderpath, video_id, window, use_xml):
    """
    Analyse a video.

    videopath(String): Full path to the processed video.

    xmlpath(String): Full path to the XML File.

    folderpath(String): Full path to the folder to store results in.

    video_id(String): ID of the processing video.

    window(Qt Window object): The Window where the UI for the analysation is in.

    use_xml(Bool): Whether to use an xml file for the video starting time.
    """

    with open("files/settings.data", "r") as settings_file:
        settings = json.loads(settings_file.read())
        blur, x_grid, y_grid, thresh_value, thresh_max_brightness, dilate, max_meteors, min_area, max_area, \
        signal_label, sort_out_area_difference, max_length, min_length, resolution_to_write = settings[:-4]

    try:
        os.rename(src=f'{folderpath}/{video_id}', dst=f'{folderpath}/remove')
    except FileNotFoundError:
        pass

    shutil.rmtree(f'{folderpath}/remove', ignore_errors=True)

    try:
        os.mkdir(f'{folderpath}/{video_id}')
    except FileExistsError:
        pass

    if use_xml:
        # Reading and processing the XML-file
        try:
            xml_file = minidom.parse(xmlpath)
        except FileNotFoundError:
            xml_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected XML file does not exist.")
            xml_not_found.setWindowTitle("XML not found")
            xml_not_found.exec_()
            return False, {}, []
        try:
            creation_date = xml_file.getElementsByTagName('CreationDate')
            creation_date = creation_date[0].attributes['value'].value

            year, month, day, hour, minute, second = int(creation_date[:4]), int(creation_date[5:7]), int(
                creation_date[8:10]), int(creation_date[11:13]), int(creation_date[14:16]), int(creation_date[17:19])
        except IndexError:
            xml_not_valid = QMessageBox(icon=QMessageBox.Critical,
                                        text='The selected XML file is not valid, the key "creationDate" and its '
                                             'value is missing.')
            xml_not_valid.setWindowTitle("XML not valid")
            xml_not_valid.exec_()
            return False, {}, []

        base_time = datetime.datetime(year, month, day, hour, minute, second)
    else:
        base_time = window.base_time

    resolution = (window.Width, window.Height)
    length = window.length
    window.len_mul = resolution[1] // 1080
    window.ar_mul = window.len_mul ** 2

    len_mul = window.len_mul
    ar_mul = window.ar_mul

    saved_model_path = "files/tensorflow/saved_model"

    print("Loading the Tensorflow model...", end=" ")
    detect_fn = tf.saved_model.load(saved_model_path)
    print("Done")

    detections_list = []
    meteor_data = {}

    if os.path.isfile(videopath):
        video = FileVideoStream(path=videopath, start_frame=window.start_frame).start()
    else:
        video_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected Video does not exist.")
        video_not_found.setWindowTitle("Video not found")
        video_not_found.exec_()
        return False, {}, []

    print(f"Detected a resolution of {resolution[0]}x{resolution[1]} for {os.path.basename(videopath)}")
    frame_number = window.start_frame
    iteration = 0

    window.analysation_status_image.setMovie(window.loading_animation)
    window.loading_animation.start()

    window.analysation_progressdialog = QProgressDialog(
        "Analysing the video... \n\nEstimated remaining time: \nCalculating...", "Exit", 1, 100, window)
    window.analysation_progressdialog.setWindowTitle("Analysing...")
    window.analysation_progressdialog.setMinimumWidth(500)
    window.analysation_progressdialog.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
    window.analysation_progressdialog.setObjectName("default_widget")

    t = QTime()
    t.start()
    frames_since_reset = 1

    for i in range(length - window.start_frame):
        frames_since_reset += 1
        if frame_number % 100 == 0:
            t.restart()
            frames_since_reset = 1
        progress_percent = frame_number / length * 100
        window.analysation_progressdialog.setValue(int(progress_percent))
        print(window.analysation_progressdialog.value())
        window.remaining_seconds = round((length - frame_number) * ((t.elapsed() / frames_since_reset) / 1000)) + 1
        window.remaining_time = str(datetime.timedelta(seconds=window.remaining_seconds))
        window.analysation_progressdialog.setLabelText(
            f"Analysing the video... \n\nEstimated remaining time: \n{window.remaining_time} s")
        iteration += 1

        start_time = time.time()

        image_np = video.read()

        if image_np is None:
            break

        slice_ranges = [
            [0, resolution[1]//2, 0, resolution[0]//2],
            [0, resolution[1]//2, resolution[0]//2, resolution[0]],
            [resolution[1]//2, resolution[1], 0, resolution[0]//2],
            [resolution[1]//2, resolution[1], resolution[0]//2, resolution[0]]
        ]

        for slice_range in slice_ranges:
            print("Slice range", slice_range)
            image = image_np[slice_range[0]:slice_range[1], slice_range[2]:slice_range[3]]

            try:
                input_tensor = tf.convert_to_tensor(image)
            except ValueError as e:
                print("Image could not be loaded:", e)
                continue
            input_tensor = input_tensor[tf.newaxis, ...]

            inference_start = time.perf_counter()
            detections = detect_fn(input_tensor)

            num_detections = int(detections.pop("num_detections"))
            detections = {key: value[0, :num_detections].numpy()
                        for key, value in detections.items()}
            detections["num_detections"] = num_detections

            detections["detection_classes"] = detections["detection_classes"].astype(np.int64)

            valid_boxes = {}
            for index, score in enumerate(detections["detection_scores"]):
                if score < 0.15:
                    continue
                boxes = detections["detection_boxes"][index]
                coordinates = [round(slice_range[0] + boxes[0] * resolution[1]), round(slice_range[0] + boxes[1] * resolution[0]),
                            round(slice_range[2] + boxes[2] * resolution[1]), round(slice_range[2] + boxes[3] * resolution[0])]
                if calculate_area(coordinates) < max_area * ar_mul:
                    valid_boxes[score] = coordinates

            detections_list.append(valid_boxes)

        frame_number += 1

        print(f"Frame {i + 1} took {round(time.time() - start_time, 4)} seconds to analyse")

    video.stop()

    replacing_list = []
    for detection in detections_list:
        boxes = list(detection.values())

        if len(boxes) <= 1:
            replacing_list.append([])
            continue

        overlapping_boxes = []
        boxes_copy = boxes.copy()
        for i, box_pts in enumerate(boxes):
            boxes_copy.remove(box_pts)
            for i2, second_box_pts in enumerate(boxes_copy):
                if box_overlap(box_pts, second_box_pts, resolution, padding=5):
                    extending_success = False
                    for index, existing_overlaping_boxes in enumerate(overlapping_boxes):
                        if i in existing_overlaping_boxes or boxes.index(second_box_pts) in existing_overlaping_boxes:
                            overlapping_boxes[index].extend([i, boxes.index(second_box_pts)])
                            extending_success = True
                            break
                    if not extending_success:
                        overlapping_boxes.append([i, boxes.index(second_box_pts)])

        overlapping_boxes = [sorted(list(set(x))) for x in overlapping_boxes]

        if len(overlapping_boxes) == 0:
            replacing_list.append([])
            continue
        replacing_list_current_frame = []
        for separate_box in overlapping_boxes:
            x_values = []
            y_values = []
            for index in separate_box:
                x_values.extend([boxes[index][1], boxes[index][3]])
                y_values.extend([boxes[index][0], boxes[index][2]])
            new_coordinates = [min(y_values), min(x_values), max(y_values), max(x_values)]

            replacing_scores = [list(detection.keys())[x] for x in separate_box]
            replacing_list_current_frame.append([replacing_scores, [max(replacing_scores), new_coordinates]])

        replacing_list.append(replacing_list_current_frame)

    for index, item in enumerate(replacing_list):
        if len(item) == 0:
            continue
        for boxes_to_replace in item:
            for score in boxes_to_replace[0]:
                try:
                    del detections_list[index][score]
                except KeyError as e:
                    print(str(e))
                    print(detections_list[index])

            detections_list[index][boxes_to_replace[1][0]] = boxes_to_replace[1][1]

    detection_count = 0
    for i, detection in enumerate(detections_list):
        if len(detection) == 0:
            continue
        for score in detection.keys():
            detection_count += 1
            y1, x1, y2, x2 = detection[score]
            box_coordinates_xy = [x1, y1, x2, y2]
            meteor_data[f"signal_{detection_count}"] = {
                "VideoID": video_id,
                "box_coordinates": box_coordinates_xy,
                "frame": [i + 1],
                "area": calculate_area(box_coordinates_xy),
                "rotation": 0,
            }

    print(detections_list)
    # TODO: Remove after use for debugging
    with open(os.path.join(folderpath, f"detections_list_{video_id}.txt"), "w") as f:
        # f.write(json.dumps(detections_list) + "\n" + json.dumps(meteor_data))
        f.write(json.dumps(meteor_data))
    cap = cv2.VideoCapture(videopath)
    for i, data in enumerate(detections_list):
        x, image = cap.read()
        image_resized = cv2.resize(image, (1940, 1080))
        if len(data.keys()) != 0:
            for box in list(data.values()):
                image_resized = cv2.rectangle(image_resized, (box[1] // 2, box[0] // 2), (box[3] // 2, box[2] // 2), (255, 255, 255), 1)
            cv2.imwrite(os.path.join(folderpath, f"{video_id}/{i + 1}-analysed.jpg"), image_resized)
    cap.release()

    return True, meteor_data, [], convert_datetime(base_time)


def analyse_diff(videopath, xmlpath, folderpath, video_id, window, use_xml):
    """
    Analyse a video. 
    
    videopath(String): Full path to the processed video. 
    
    xmlpath(String): Full path to the XML File. 
    
    folderpath(String): Full path to the folder to store results in. 
    
    VideoID(String): ID of the processing video. 
    
    window(Qt Window object): The Window where the UI for the analysation is in.
    
    use_xml(Bool): Whether to use an xml file for the video starting time.
    """

    # Reading Files
    if os.path.isfile(videopath):
        video = FileVideoStream(path=videopath, start_frame=window.start_frame).start()
    else:
        video_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected Video does not exist.")
        video_not_found.setWindowTitle("Video not found")
        video_not_found.exec_()
        return False, {}, []

    with open("files/settings.data", "r") as settings_file:
        settings = json.loads(settings_file.read())
        blur, x_grid, y_grid, thresh_value, thresh_max_brightness, dilate, max_meteors, min_area, max_area, \
        signal_label, sort_out_area_difference, max_length, min_length, resolution_to_write = settings[:-4]

    black = cv2.imread('files/black.png', 0)

    try:
        os.rename(src=f'{folderpath}/frames', dst=f'{folderpath}/remove')
        os.rename(src=f'{folderpath}/trash', dst=f'{folderpath}/remove2')
        os.rename(src=f'{folderpath}/diff', dst=f'{folderpath}/remove3')
    except FileNotFoundError:
        pass

    shutil.rmtree(f'{folderpath}/remove', ignore_errors=True)
    shutil.rmtree(f'{folderpath}/remove2', ignore_errors=True)
    shutil.rmtree(f'{folderpath}/remove3', ignore_errors=True)

    try:
        os.mkdir(f'{folderpath}/frames')
        os.mkdir(f'{folderpath}/trash')
        os.mkdir(f'{folderpath}/diff')
    except FileExistsError:
        pass

    # Defining the variable for the reference frame
    ref_frame = None

    global MeteorID_List
    MeteorID_List = []
    rotation_list = []
    meteor_area_list = []
    pause_analysation = False

    status_list = [None, None]
    sort_out_list = []

    length = window.length
    fps = window.Fps
    height = window.Height
    width = window.Width

    if use_xml:
        # Reading and processing the XML-file
        try:
            xml_file = minidom.parse(xmlpath)
        except FileNotFoundError:
            xml_not_found = QMessageBox(icon=QMessageBox.Critical, text="The selected XML file does not exist.")
            xml_not_found.setWindowTitle("XML not found")
            xml_not_found.exec_()
            return False, {}, []
        try:
            creation_date = xml_file.getElementsByTagName('CreationDate')
            creation_date = creation_date[0].attributes['value'].value

            year, month, day, hour, minute, second = int(creation_date[:4]), int(creation_date[5:7]), int(
                creation_date[8:10]), int(creation_date[11:13]), int(creation_date[14:16]), int(creation_date[17:19])
        except IndexError:
            xml_not_valid = QMessageBox(icon=QMessageBox.Critical,
                                        text='The selected XML file is not valid, the key "creationDate" and its '
                                             'value is missing.')
            xml_not_valid.setWindowTitle("XML not valid")
            xml_not_valid.exec_()
            return False, {}, []

        base_time = datetime.datetime(year, month, day, hour, minute, second)
    else:
        base_time = window.base_time

    window.len_mul = height // 1080
    window.ar_mul = window.len_mul ** 2

    len_mul = window.len_mul
    ar_mul = window.ar_mul

    # Defining the variable for the current frame
    frame_number = window.start_frame
    # video.set(cv2.CAP_PROP_POS_FRAMES, window.start_frame)

    detection_count = 0

    meteor_data = {}

    window.analysation_status_image.setMovie(window.loading_animation)
    window.loading_animation.start()

    window.analysation_progressdialog = QProgressDialog(
        "Analysing the video... \n\nEstimated remaining time: \nCalculating...", "Exit", 1, 100, window)
    window.analysation_progressdialog.setWindowTitle("Analysing...")
    window.analysation_progressdialog.setMinimumWidth(500)
    window.analysation_progressdialog.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
    window.analysation_progressdialog.setObjectName("default_widget")

    t = QTime()
    t.start()
    frames_since_reset = 1

    for i in range(length - window.start_frame):
        frames_since_reset += 1
        if frame_number % 100 == 0:
            t.restart()
            frames_since_reset = 1
        progress_percent = frame_number / length * 100
        window.analysation_progressdialog.setValue(int(progress_percent))
        window.remaining_seconds = round((length - frame_number) * ((t.elapsed() / frames_since_reset) / 1000)) + 1
        window.remaining_time = str(datetime.timedelta(seconds=window.remaining_seconds))
        window.analysation_progressdialog.setLabelText(
            f"Analysing the video... \n\nEstimated remaining time: \n{window.remaining_time} s")

        # Reading current frame
        frame = video.read()

        # Calculating the time
        current_seconds = frame_number / fps

        time_to_display = base_time + timedelta(seconds=current_seconds)

        if pause_analysation:
            # Resize the main window to match the screen size
            frame_resized = cv2.resize(frame, (1280, 720))

            # Writing the text for the time, date and frame number
            cv2.putText(frame_resized, str(time_to_display)[:-5], (20, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5,
                        (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(frame_resized, str(frame_number), (1220, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1,
                        cv2.LINE_AA)

            # Drawing and writing the text for the grid
            cv2.putText(frame_resized, 'A', (70, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame_resized, 'B', (70 + 160, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, 'C', (70 + 320, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, 'D', (70 + 480, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, 'E', (70 + 640, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, 'F', (70 + 800, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, 'G', (70 + 960, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, 'H', (70 + 1120, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, '1', (15, 80), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.putText(frame_resized, '2', (15, 80 + 144), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, '3', (15, 80 + 288), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, '4', (15, 80 + 432), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)
            cv2.putText(frame_resized, '5', (15, 80 + 576), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1,
                        cv2.LINE_AA)

            cv2.putText(frame_resized,
                        'Press "esc" to exit, "P" to pause the analysation and "R" to set a new reference frame',
                        (300, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.imshow('VAMOS - Analysation', frame_resized)
            key = cv2.waitKey(1)

            if key == 27 or window.analysation_progressdialog.wasCanceled():
                window.broke_frame = frame_number
                break

            if key == ord('p'):
                pause_analysation = not pause_analysation

            frame_number += 1
            continue

        # Reset variables
        status = 0
        trash_frame = False

        # Preparing the Video for calculations
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (blur * len_mul + 1, 20 * len_mul + 1), 0)

        if ref_frame is None:
            ref_frame = gray
            status_list = [0]
            frame_number += 1
            continue
        if frame_number % 375 == 0:
            ref_frame = gray

        width = width // x_grid
        height = height // y_grid
        for v in range(y_grid):
            move = v * height
            for h in range(x_grid):
                cv2.rectangle(frame, (width * h, move), (width * (h + 1), move + height), (100, 100, 100), 1)

        # Calculating the difference between the current frame and the reference frame
        delta_frame = cv2.subtract(gray, ref_frame)

        thresh_delta = cv2.threshold(delta_frame, thresh_value, thresh_max_brightness, cv2.THRESH_BINARY)[1]

        thresh_delta = cv2.dilate(thresh_delta, None, iterations=dilate)

        (cnts, _) = cv2.findContours(thresh_delta.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Drawing boxes around areas that have a detection
        if len(cnts) > max_meteors:
            ref_frame = gray
            print(f"Frame was reset because more than {max_meteors} {signal_label}s")
            frame_number += 1
            continue
        else:
            for contour in cnts:
                if cv2.contourArea(contour) < min_area * ar_mul or cv2.contourArea(contour) > max_area * ar_mul:
                    continue
                status = 1
                detection_count += 1
                meteor_area_list.append(cv2.contourArea(contour))
                rect = cv2.minAreaRect(contour)
                rotation_list.append(rect[2])
                (x, y, w, h) = cv2.boundingRect(contour)
                border = 10 * len_mul
                text_border = 20 * len_mul
                # cv2.rectangle(frame, (x - border, y - border), (x + w + border, y + h + border), (255, 255, 255), 2)
                box = cv2.boxPoints(rect)
                box = numpy.int0(box)
                cv2.drawContours(frame, [box], 0, (0, 0, 255), 2)
                cv2.putText(frame, signal_label, (x - border, y - text_border), cv2.FONT_HERSHEY_SIMPLEX, 1 * len_mul,
                            (100, 255, 0), 1, cv2.LINE_AA)
                average_x = x + (w // 2)
                average_y = y + (h // 2)
                meteor_data[f"signal_{detection_count}"] = {
                    "VideoID": video_id,
                    "position": (average_x, average_y),
                    "frame": [frame_number],
                    "area": cv2.contourArea(contour),
                    "rotation": rect[2],
                }

        # Return if a meteor was detected
        status_list.append(status)
        status_list = status_list[-3:]

        if i != 1 and status == 1:
            try:
                diff = cv2.absdiff(thresh_delta, thresh_delta_previous)
                diff_px = numpy.sum(diff == 255)
                diff_to_write = cv2.resize(diff, (1280, 720))
                cv2.putText(diff_to_write, str(diff_px), (1220, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1,
                            cv2.LINE_AA)
                cv2.imwrite(f"{folderpath}/diff/{frame_number}_diff.png", diff_to_write)
                if 0 < diff_px < sort_out_area_difference * ar_mul:
                    sort_out_list.append(frame_number)
                    print(frame_number, diff_px, f"is smaller than {sort_out_area_difference * ar_mul}")
                    trash_frame = True
                else:
                    print(status_list[-2])
                    print(frame_number, diff_px, f"is bigger than {sort_out_area_difference * ar_mul}")
            except UnboundLocalError:
                thresh_delta_previous = thresh_delta
                diff = cv2.absdiff(thresh_delta, thresh_delta_previous)

        thresh_delta_previous = thresh_delta

        if status_list[-1] == 1 and status_list[-2] == 0:  # If the meteor appeared
            window.meteor_count += 1

        # Resize the main window to match the screen size
        frame_resized = cv2.resize(frame, (1280, 720))

        # Writing the text for the time, date and frame number
        cv2.putText(frame_resized, str(time_to_display)[:-5], (20, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200),
                    1, cv2.LINE_AA)
        cv2.putText(frame_resized, str(frame_number), (1220, 700), cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1,
                    cv2.LINE_AA)

        # Drawing and writing the text for the grid
        cv2.putText(frame_resized, 'A', (70, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, 'B', (70 + 160, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, 'C', (70 + 320, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, 'D', (70 + 480, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, 'E', (70 + 640, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, 'F', (70 + 800, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, 'G', (70 + 960, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, 'H', (70 + 1120, 25), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, '1', (15, 80), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, '2', (15, 80 + 144), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, '3', (15, 80 + 288), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, '4', (15, 80 + 432), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(frame_resized, '5', (15, 80 + 576), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

        if status == 1:
            frame_to_write = cv2.resize(frame_resized, tuple(resolution_to_write))
            frame_to_write = cv2.cvtColor(frame_to_write, cv2.COLOR_BGR2GRAY)
            if trash_frame:
                cv2.imwrite(f"{folderpath}/trash/{frame_number}_frame.png", frame_to_write)
            else:
                cv2.imwrite(f"{folderpath}/frames/{frame_number}_frame.png", frame_to_write)

        cv2.putText(frame_resized,
                    'Press "esc" to exit, "P" to pause the analysation and "R" to set a new reference frame',
                    (300, 700),
                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

        # Resize windows for stack
        gray_resized = cv2.resize(gray, (864, 486))
        thresh_resized = cv2.resize(thresh_delta, (864, 486))
        delta_resized = cv2.resize(delta_frame, (864, 486))
        black_resized = cv2.resize(black, (864, 486))

        # Stack the Windows that provide extra detail
        stack1 = numpy.hstack([gray_resized, thresh_resized])
        stack2 = numpy.hstack([delta_resized, black_resized])
        stack = numpy.vstack([stack1, stack2])
        cv2.rectangle(stack, (0, 0), (864, 486), (255, 255, 255), 1)
        cv2.rectangle(stack, (0, 486), (864, 971), (255, 255, 255), 1)
        cv2.rectangle(stack, (864, 0), (1727, 486), (255, 255, 255), 1)
        cv2.putText(stack, 'Difference', (350, 520), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(stack, 'Capturing', (350, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(stack, 'Threshold', (1250, 30), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1, cv2.LINE_AA)

        # Opening windows for visualization
        cv2.imshow('VAMOS - Analysation', frame_resized)

        # try:
        #     cv2.imshow('VAMOS - Difference', diff_to_write)
        # except UnboundLocalError:
        #     pass
        cv2.imshow('VAMOS - Additional details', stack)

        key = cv2.waitKey(1)

        if key == 27 or window.analysation_progressdialog.wasCanceled():
            window.broke_frame = frame_number
            break

        if key == ord('r'):
            ref_frame = gray
            print("Frame reset because of key pressed.")

        if key == ord('p'):
            pause_analysation = True

        frame_number += 1

    window.analysation_progressdialog.setValue(100)

    video.stop()

    print("Done at:", datetime.datetime.now())

    # Close all Windows
    # cv2.destroyWindow('VAMOS - Analysation')
    # cv2.destroyWindow('VAMOS - Additional details')
    # cv2.destroyWindow('VAMOS - Difference')

    return True, meteor_data, sort_out_list, convert_datetime(base_time)


def apply_defaults(window):
    with open("files/defaults.data", "r") as defaults_file:
        defaults = json.loads(defaults_file.read())

    if defaults[0] == [] or defaults[1] == [] or defaults[2] == "None":
        set_defaults_now = QMessageBox.question(window, "No defaults yet!",
                                                "You have not set any defaults yet. Do you want to set them now?",
                                                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if set_defaults_now == QMessageBox.Yes:
            set_defaults(window)
    else:
        window.videopath_list, window.xmlpath_list, window.folderpath = defaults
        window.setup_video_selection(window.videopath_list)
        window.setup_xml_selection(window.xmlpath_list)
        window.setup_folder_selection(window.folderpath)


def set_defaults(window):
    select_video_info = QMessageBox(icon=QMessageBox.Information,
                                    text="In the following dialog, select your default video(s).")
    select_video_info.setWindowTitle("Info")
    select_video_info.exec_()

    window.default_videopath_list = QFileDialog.getOpenFileNames(parent=window, filter="MP4 Files (*.mp4)")
    window.default_videopath_list = window.default_videopath_list[0]
    if window.default_videopath_list:  # If the user didn't cancel the selection
        select_xml_info = QMessageBox(icon=QMessageBox.Information,
                                      text="In the following dialog, select your default XML(s).")
        select_xml_info.setWindowTitle("Info")
        select_xml_info.exec_()

        window.default_xmlpath_list = QFileDialog.getOpenFileNames(parent=window, filter="XML Files (*.xml)")
        window.default_xmlpath_list = window.default_xmlpath_list[0]
        if window.default_xmlpath_list:  # If the user didn't cancel the selection
            select_folder_info = QMessageBox(icon=QMessageBox.Information,
                                             text="In the following dialog, select your default folder to store "
                                                  "results in.")
            select_folder_info.setWindowTitle("Info")
            select_folder_info.exec_()

            window.default_folderpath = QFileDialog.getExistingDirectory(parent=window)
            if window.default_folderpath != "":  # If the user didn't cancel the selection
                default_paths = [window.default_videopath_list, window.default_xmlpath_list, window.default_folderpath]
                with open("files/defaults.data", "w") as defaults_file:
                    defaults_file.write(json.dumps(default_paths))

                set_defaults_success_message = QMessageBox(icon=QMessageBox.Information,
                                                           text="Defaults set successfully!")
                set_defaults_success_message.setWindowTitle("Info")
                set_defaults_success_message.exec_()


def delete_defaults(window):
    delete_continue = QMessageBox.question(window, "Do you want to delete?",
                                           "Are you sure that you want to delete the defaults?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

    if delete_continue == QMessageBox.Yes:
        none_content = [[], [], "None"]
        with open("files/defaults.data", "w") as defaults_file:
            defaults_file.write(json.dumps(none_content))

        set_defaults_success_message = QMessageBox(icon=QMessageBox.Information, text="Defaults deleted successfully!")
        set_defaults_success_message.setWindowTitle("Info")
        set_defaults_success_message.exec_()


def get_thumbnail(path):
    if os.path.isfile(path):
        vid = FileVideoStream(path).start()
    else:
        video_title = os.path.split(path)[1]
        video_not_found = QMessageBox(icon=QMessageBox.Critical, text=f"The video {video_title} was not found!")
        video_not_found.setWindowTitle("Video not found")
        video_not_found.exec_()
        return numpy.array(None)
    thumbnail = vid.read()
    vid.stop()
    thumbnail = cv2.resize(thumbnail, (240, 135))
    return thumbnail


def generate_results_old(fps, meteor_data, sort_out_list, len_mul):
    if meteor_data == {}:
        return {}

    with open("files/settings.data", "r") as settings_file:
        settings = json.loads(settings_file.read())
        min_area, max_area, _, _, max_length, min_length, _, max_distance, max_frames, delete_threshold, \
        delete_percentage = settings[-11:]
    meteors = {}
    x_positions_list = []
    y_positions_list = []
    area_list = []
    rotation_list = []
    meteor_list_count = 1

    for key in meteor_data.keys():
        if key[:6] != "signal":
            continue
        if key == "signal_1":
            current_position = meteor_data[key]['position']
            current_frame = meteor_data[key]['frame']
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            area_list.append(meteor_data[key]['area'])
            rotation_list.append(meteor_data[key]['rotation'])
            signal_time = (datetime.datetime.fromtimestamp(current_frame[0] / fps) - timedelta(hours=1)).time()
            current_video_id = meteor_data[key]['VideoID']
            current_time = datetime.datetime(*meteor_data[current_video_id]) + timedelta(
                seconds=current_frame[0] / fps)
            meteors["M-" + "%07d" % meteor_list_count] = {
                "VideoID": current_video_id,
                "position": current_position,
                "frames": current_frame,
                "beginning": [convert_datetime(current_time.time()),
                              convert_datetime(signal_time)],
                "end": [],
                "duration": [],
                "area": meteor_data[key]['area'],
                "rotation": meteor_data[key]['rotation'],
                "date": convert_datetime(current_time.date())
            }
            continue
        previous_position = current_position
        current_position = meteor_data[key]['position']
        current_frame = meteor_data[key]['frame']
        if check_pos(current_position, previous_position, max_distance * len_mul) and \
                abs(current_frame[0] - meteors["M-" + "%07d" % meteor_list_count]["frames"][-1]) <= 10:
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            area_list.append(meteor_data[key]['area'])
            rotation_list.append(meteor_data[key]['rotation'])
            meteors["M-" + "%07d" % meteor_list_count]["frames"].append(current_frame[0])
            signal_time = (datetime.datetime.fromtimestamp(current_frame[0] / fps) - timedelta(hours=1)).time()
            current_time = datetime.datetime(*meteor_data[current_video_id]) + timedelta(
                seconds=current_frame[0] / fps)
        else:
            meteors["M-" + "%07d" % meteor_list_count]["position"] = (
                int(statistics.mean(x_positions_list)), int(statistics.mean(y_positions_list)))
            meteors["M-" + "%07d" % meteor_list_count]["frames"] = sorted(
                set(meteors["M-" + "%07d" % meteor_list_count]["frames"]))
            meteors["M-" + "%07d" % meteor_list_count]["rotation"] = round(statistics.mean(set(rotation_list)))
            meteors["M-" + "%07d" % meteor_list_count]["area"] = sorted(area_list)[-1]
            meteors["M-" + "%07d" % meteor_list_count]["end"] = [convert_datetime(current_time.time()),
                                                                 convert_datetime(signal_time)]
            current_duration = current_time - datetime.datetime(
                *meteors["M-" + "%07d" % meteor_list_count]["date"],
                *meteors["M-" + "%07d" % meteor_list_count]["beginning"][0]
            )
            meteors["M-" + "%07d" % meteor_list_count]["duration"] = [int(
                current_duration.total_seconds() * fps), convert_datetime(current_duration)]
            x_positions_list.clear()
            y_positions_list.clear()
            area_list.clear()
            rotation_list.clear()
            meteor_list_count += 1
            x_positions_list.append(current_position[0])
            y_positions_list.append(current_position[1])
            area_list.append(meteor_data[key]['area'])
            rotation_list.append(meteor_data[key]['rotation'])
            signal_time = (datetime.datetime.fromtimestamp(current_frame[0] / fps) - timedelta(hours=1)).time()
            current_video_id = meteor_data[key]['VideoID']
            current_time = datetime.datetime(*meteor_data[current_video_id]) + timedelta(
                seconds=current_frame[0] / fps)
            meteors["M-" + "%07d" % meteor_list_count] = {
                "VideoID": current_video_id,
                "position": current_position,
                "frames": current_frame,
                "beginning": [convert_datetime(current_time.time()),
                              convert_datetime(signal_time)],
                "end": [],
                "duration": [],
                "area": meteor_data[key]['area'],
                "rotation": meteor_data[key]['rotation'],
                "date": convert_datetime(current_time.date())
            }

    meteors["M-" + "%07d" % meteor_list_count]["position"] = (
        int(statistics.mean(x_positions_list)), int(statistics.mean(y_positions_list)))
    meteors["M-" + "%07d" % meteor_list_count]["frames"] = sorted(
        set(meteors["M-" + "%07d" % meteor_list_count]["frames"]))
    meteors["M-" + "%07d" % meteor_list_count]["rotation"] = round(statistics.mean(set(rotation_list)))
    meteors["M-" + "%07d" % meteor_list_count]["area"] = sorted(area_list)[-1]
    meteors["M-" + "%07d" % meteor_list_count]["end"] = [convert_datetime(current_time.time()),
                                                         convert_datetime(signal_time)]
    current_duration = current_time - datetime.datetime(
        *meteors["M-" + "%07d" % meteor_list_count]["date"],
        *meteors["M-" + "%07d" % meteor_list_count]["beginning"][0]
    )
    meteors["M-" + "%07d" % meteor_list_count]["duration"] = [int(current_duration.total_seconds() * fps),
                                                              convert_datetime(current_duration)]

    meteors_updated = {}
    delete_keys = []

    # Remove the sorted out meteor signals
    for key in meteors:
        indications = 0
        frames = meteors[key]["frames"]
        area = meteors[key]["area"]
        for frame in frames:
            if frame in sort_out_list:
                indications += 1
        if len(frames) <= max_frames and indications > 0:  # If it is a very short meteor with indications, delete it.
            print(f"less than {max_frames} and has indications")
            delete_keys.append(key)
        elif indications > delete_threshold:
            print(f"more than {delete_threshold} indications")
            delete_keys.append(key)
        elif indications / len(frames) >= delete_percentage:  # If more than 25% of the frames were marked, delete it.
            print(f"more than {delete_percentage * 100}%")
            delete_keys.append(key)
        elif len(frames) <= min_length * fps or len(frames) > max_length * fps:
            print(
                f"Duration of {len(frames)} is shorter than {min_length * fps} or longer than {max_length * fps} frames")
            delete_keys.append(key)
        elif min_area < area > max_area:
            print(f"Area of {area} px is smaller than {min_area} px or bigger than {max_area} px")
            delete_keys.append(key)

    # for key in delete_keys:
    #     del meteors[key]

    for i, key in enumerate(meteors):
        meteors_updated["M-" + "%07d" % (i + 1)] = meteors[key]

    return meteors_updated


def generate_results(fps, meteor_data, sort_out_list, len_mul):
    if meteor_data == {}:
        return {}

    with open("files/settings.data", "r") as settings_file:
        settings = json.loads(settings_file.read())
        min_area, max_area, _, _, max_length, min_length, _, max_distance, max_frames, delete_threshold, \
        delete_percentage = settings[-11:]
    meteors = {}
    meteor_list_count = 1

    for video_id in meteor_data.keys():
        for key in meteor_data[video_id].keys():
            success = False
            if key[:6] != "signal":
                continue
            signal = meteor_data[video_id][key]
            existing_meteors = list(meteors.keys())
            existing_meteors.reverse()
            for existing_meteor in existing_meteors:
                if len(meteors) == 0:
                    break
                if abs(meteors[existing_meteor]["frames"][-1] - signal["frame"][0]) <= 200 and check_pos(
                        calculate_center(signal["box_coordinates"]),
                        calculate_center(meteors[existing_meteor]["box_coordinates"][-1]), max_distance * len_mul):
                    if abs(meteors[existing_meteor]["frames"][-1] - signal["frame"][0]) > 20:
                        meteors[existing_meteor]["sort_out"] = True
                    meteors[existing_meteor]["frames"].append(signal["frame"][0])
                    meteors[existing_meteor]["area"].append(signal["area"])
                    meteors[existing_meteor]["box_coordinates"].append(signal["box_coordinates"])
                    success = True
                    break
            if not success:  # Current frame could not be assigned to previous meteor
                meteors["M-" + "%07d" % meteor_list_count] = {
                    "VideoID": signal["VideoID"],
                    "box_coordinates": [signal["box_coordinates"]],
                    "frames": signal["frame"],
                    "area": [signal["area"]],
                    "rotation": [signal["rotation"]],
                    "sort_out": False,
                }
                meteor_list_count += 1
                existing_meteors.reverse()
                # for existing_meteor in existing_meteors:
                #     if len(meteors) == 0:
                #         break
                #     if abs(meteors[existing_meteor]["frames"][-1] - signal["frame"][0]) <= 10 and check_pos(
                #             calculate_center(signal["box_coordinates"]),
                #             calculate_center(meteors[existing_meteor]["box_coordinates"][-1]), max_distance * len_mul):
                #         meteors[existing_meteor]["frames"].append(signal["frame"][0])
                #         meteors[existing_meteor]["area"].append(signal["area"])
                #         meteors[existing_meteor]["box_coordinates"].append(signal["box_coordinates"])
                #         success = True
                #         break
                # if not success:
                #     meteors["M-" + "%07d" % meteor_list_count] = {
                #         "VideoID": signal["VideoID"],
                #         "box_coordinates": [signal["box_coordinates"]],
                #         "frames": signal["frame"],
                #         "area": [signal["area"]],
                #         "rotation": [signal["rotation"]],
                #     }
                #     meteor_list_count += 1

    for meteor in meteors.keys():
        meteors[meteor]["position"] = calculate_mean_position(meteors[meteor]["box_coordinates"])
        meteors[meteor]["area"] = max(meteors[meteor]["area"])
        meteors[meteor]["rotation"] = statistics.mean(meteors[meteor]["rotation"])
        meteors[meteor]["duration"] = max(meteors[meteor]["frames"]) - min(meteors[meteor]["frames"]) + 1
        beginning = convert_datetime(
            datetime.datetime(*meteor_data[meteors[meteor]["VideoID"]][meteors[meteor]["VideoID"]]) +
            timedelta(seconds=min(meteors[meteor]["frames"]) / fps))
        meteors[meteor]["beginning"] = [beginning[-4:],
                                        convert_datetime(timedelta(seconds=min(meteors[meteor]["frames"]) / fps))]
        meteors[meteor]["end"] = [
            convert_datetime(datetime.datetime(*meteor_data[meteors[meteor]["VideoID"]][meteors[meteor]["VideoID"]]) +
                             timedelta(seconds=(max(meteors[meteor]["frames"]) + 1) / fps))[-4:],
            convert_datetime(timedelta(seconds=(max(meteors[meteor]["frames"]) + 1) / fps))]
        meteors[meteor]["date"] = beginning[:3]

    meteors_updated = {}
    delete_keys = []

    for key in meteors:
        duration = meteors[key]["duration"]
        if meteors[key]["sort_out"]:
            delete_keys.append(key)
            continue
        # area = meteors[key]["area"]
        if duration > max_length * fps:
            print(
                f"Duration of {duration} is longer than {max_length * fps} frames")
            delete_keys.append(key)
        elif duration < min_length * fps:
            print(
                f"Duration of {duration} is shorter than {min_length * fps} frames")
            delete_keys.append(key)
        # elif min_area < area > max_area:
        #     print(f"Area of {area} px is smaller than {min_area} px or bigger than {max_area} px")
        #     delete_keys.append(key)

    # Remove the sorted out meteor signals
    for key in delete_keys:
        del meteors[key]

    for i, key in enumerate(meteors):
        meteors_updated["M-" + "%07d" % (i + 1)] = meteors[key]

    return meteors_updated


def convert_datetime(dobject):
    if type(dobject) == datetime.date:
        return [dobject.year, dobject.month, dobject.day]
    if type(dobject) == datetime.datetime:
        return [dobject.year, dobject.month, dobject.day, dobject.hour, dobject.minute, dobject.second,
                dobject.microsecond]
    if type(dobject) == datetime.time:
        return [dobject.hour, dobject.minute, dobject.second, dobject.microsecond]
    if type(dobject) == datetime.timedelta:
        return [dobject.seconds // 3600, (dobject.seconds // 60) % 60, dobject.seconds % 60,
                int((round(dobject.total_seconds() % 1, 2)) * 1000000)]


def write_vamos_file(fps, vamos_filepath, meteor_data, sort_out_list, base_time_list, videopath_list,
                     xmlpath_list, folderpath, duration_list, fps_list, resolution_list):
    file_string = ""
    file_string += json.dumps([videopath_list, xmlpath_list, folderpath]) + "\n"
    file_string += json.dumps(base_time_list) + "\n"
    file_string += json.dumps(duration_list) + "\n"
    file_string += json.dumps(fps_list) + "\n"
    file_string += json.dumps(resolution_list) + "\n"
    # try:
    len_mul = resolution_list[1][0] // 1080
    generated_results = generate_results(fps, meteor_data, sort_out_list, len_mul)
    file_string += json.dumps(generated_results) + "\n"
    # file_string += json.dumps(meteor_data) + "\n"
    # file_string += json.dumps(sort_out_list) + "\n"
    # except Exception as e:
    #     print(e)
    #     file_string += json.dumps(meteor_data) + "\n"
    #     file_string += json.dumps(sort_out_list) + "\n"
    with open(vamos_filepath, "w") as f:
        f.write(file_string)
    print_table(generated_results)


def print_table(input_data):
    for m in input_data.items():
        print(m[0])
        for k, v in m[1].items():
            print("{:<18} {:<25}".format(k, str(v)))
        print("\n")


def calculate_center(pts):
    y1, x1, y2, x2 = pts
    return [(y1 + y2) // 2, (x1 + x2) // 2]


def calculate_mean_position(boxes_list):
    x_positions_list = []
    y_positions_list = []
    for box in boxes_list:
        center = calculate_center(box)
        x_positions_list.append(center[0])
        y_positions_list.append(center[1])
    return [round(statistics.mean(x_positions_list)), round(statistics.mean(y_positions_list))]
