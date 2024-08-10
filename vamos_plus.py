import cv2
import datetime
import json
import os
import sys
import xml.etree.ElementTree as Et
from openpyxl import load_workbook

from PyQt5.QtCore import Qt, QSize, QAbstractTableModel, QUrl, QModelIndex, QSizeF
from PyQt5.QtGui import QFont, QIcon, QPixmap, QCursor, QImage, QMovie, QPainter, QBrush, QPen, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget, QGraphicsVideoItem
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QSpacerItem, QPushButton, QGroupBox, QHBoxLayout, \
    QVBoxLayout, QMenuBar, QMenu, QMainWindow, QApplication, QAction, QStatusBar, QFileDialog, QSizePolicy, \
    QMessageBox, QSpinBox, QDialog, QCheckBox, QRadioButton, QTableView, QSlider, QSplitter, QTabWidget, \
    QDoubleSpinBox, QLineEdit, QComboBox, QGraphicsView, QGraphicsScene

from vamos_plus_functions import analyse, analyse_diff, get_thumbnail, apply_defaults, set_defaults, delete_defaults, \
    write_vamos_file, check_pos, analyse_detections_list

StyleSheet = """
QMainWindow#AnalysationWindow {
    background-color:#121212;
    color:white;
}
QWidget#default_widget {
    background-color:#121212;
    color:white;
}
QDialog {
    background-color:#121212;
    color:white;
}
QDialog QLabel {
    background-color:#121212;
    color:white;
}
QDialog QPushButton {
    background-color:transparent;
    color:white;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:white;
    min-height: 20px;
    min-width: 60px;
}
QDialog QPushButton:default {
    background-color:transparent;
    color:#2894E0;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#2894E0;
    min-height: 20px;
    min-width: 60px;
}
QDialog QPushButton:default:hover {
    background-color:#2894E0;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#2894E0;
    min-height: 20px;
    min-width: 60px;
}
QDialog QPushButton:hover {
    background-color:white;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:white;
    min-height: 20px;
    min-width: 60px;
}
QLabel#video_thumb {
    border-style:solid;
    border-width:1px;
    border-color:#eeeeee;
}
QPushButton#secondary_button {
    background-color:transparent;
    color:#2894E0;
    border-style:solid;
    border-width:2px;
    border-radius:6px;
    border-color:#2894E0;
    padding:6px;
    max-width:80px;
    min-width:80px;
}
QPushButton#secondary_button:hover {
    background-color:#2894E0;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:6px;
    border-color:#2894E0;
    padding:6px;
    max-width:80px;
    min-width:80px;
}
QPushButton#secondary_button_wide {
    background-color:transparent;
    color:#2894E0;
    border-style:solid;
    border-width:2px;
    border-radius:6px;
    border-color:#2894E0;
    padding:6px;
    max-width:180px;
    min-width:180px;
}
QPushButton#secondary_button_wide:hover {
    background-color:#2894E0;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:6px;
    border-color:#2894E0;
    padding:6px;
    max-width:180px;
    min-width:180px;
}
QPushButton#tertiary_button {
    background-color:transparent;
    color:white;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:white;
}
QPushButton#tertiary_button:hover {
    background-color:white;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:white;
}
QGroupBox {
    background-color:transparent;
    color:white;
    border-style:solid;
    border-width:2px;
    border-radius:8px;
    border-color:white;
    padding:6px;
}
QPushButton#primary_button {
    background-color:transparent;
    color:#00BD66;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#00BD66;
    text-align:right;
    background-image:url(files/analyse_icon.png);
    background-repeat:no repeat;
    background-position:left;
    padding:10px;
}
QPushButton#primary_button:hover {
    background-color:#00BD66;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#00BD66;
    text-align:right;
    background-image:url(files/analyse_icon_hover.png);
    background-repeat:no repeat;
    background-position:left;
    padding:10px;
}
QPushButton#help_defaults_button {
    border-style:solid;
    border-width:2px;
    border-radius:16px;
    border-color:white;
    color:white;
}
QPushButton#help_defaults_button:hover {
    background-color:white;
    color:#121212;
    border-style:solid;
    border-width:2px;
    border-radius:16px;
    border-color:white;
}
QLabel#selection_status {
    max-width: 35px;
}
QPushButton#delete_button {
    background-color:transparent;
    color:#2894E0;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#2894E0;
    padding:6px;
    max-width:20px;
    background-image:url(files/trash_icon.png);
    background-repeat:no repeat;
    background-position:center;
}
QPushButton#delete_button:hover {
    background-color:#2894E0;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#2894E0;
    padding:6px;
    max-width:20px;
    background-image:url(files/trash_icon_hover.png);
    background-repeat:no repeat;
    background-position:center;
}
QLabel#default_label {
    color:#eeeeee;
}
QSpinBox#styled_spinbox{
    padding-left: 8px;
    background-color:transparent;
    color:#eeeeee;
    border-style:solid;
    border-width:2px;
    border-radius:4px;
    border-color:#eeeeee;
}
QCheckBox {
    color:#eeeeee;
}
QRadioButton {
    color:#eeeeee;
}
QToolTip {
    background:#4f5764;
    border-style: none;
    color:#b0b0b0;
    padding:4px;
}
QGridLayout {
    background-color:transparent;
}
QTableView {
    background:transparent;
    color:white;
}
QPushButton#video_button {
    background-color:transparent;
}
QSlider::groove:horizontal {
    border: 1px solid #999999;
    height: 2px; 
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
    margin: 2px 0;
}
QSlider::handle:horizontal {
    background: red;
    border: 1px solid #121212;
    width: 18px;
    height: 25px;
    margin: -10px 0px; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
    border-radius: 10px;
}
QSlider::add-page:qlineargradient {
    background: lightgrey;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
    border-top-left-radius: 0px;
    border-bottom-left-radius: 0px;
}
QSlider::sub-page:qlineargradient {
    background: red;
    border-top-right-radius: 0px;
    border-bottom-right-radius: 0px;
    border-top-left-radius: 3px;
    border-bottom-left-radius: 3px;
}
QProgressDialog QProgressBar {
    min-height: 12px;
    max-height: 12px;
    border-radius: 6px;
    text-align: center;
}
QProgressDialog QProgressBar::chunk {
    border-radius: 6px;
    background-color: #FF5500;
}
QGraphicsView {
    background-color: #121212;
    border: 0px solid #121212
}
"""


class DropLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.pathtype = ""

    def define_type(self, type_define):
        self.pathtype = type_define

    def dragEnterEvent(self, event):
        path = str(event.mimeData().urls()[0].toLocalFile())
        if event.mimeData().hasUrls and path[-4:].upper() == ".MP4" and self.pathtype == "video":
            event.accept()
        elif event.mimeData().hasUrls and path[-4:].upper() == ".XML" and self.pathtype == "xml":
            event.accept()
        elif event.mimeData().hasUrls and os.path.isdir(path) and self.pathtype == "folder":
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()

            output = event.mimeData().urls()
            links = []
            for link in output:
                if link.isLocalFile():
                    links.append(str(link.toLocalFile()))

            if self.pathtype == "video":
                Window.setup_video_selection(links)

            if self.pathtype == "xml":
                Window.setup_xml_selection(links)

            if self.pathtype == "folder":
                Window.setup_folder_selection(links[0])
        else:
            event.ignore()


class PickSpinbox(QSpinBox):
    def __init__(self, *args):
        QSpinBox.__init__(self, *args)

        self.setFont(Window.font_bold_14)
        self.setWrapping(True)
        self.setAlignment(Qt.AlignCenter)
        self.setObjectName("styled_spinbox")

    def textFromValue(self, value):
        return "%02d" % value


class DatePickerPopup(QDialog):
    def __init__(self):
        QDialog.__init__(self)

        self.setObjectName("default_widget")
        self.setWindowTitle("Select the video starting time and date")
        self.init_ui()

    def init_ui(self):
        self.now = datetime.datetime.now()

        self.datetime_group = QGroupBox(self)
        self.datetime_group.setTitle("First video")
        self.datetime_group.setFont(Window.font_normal_10)
        self.datetime_group.setFlat(True)
        self.datetime_group.setGeometry(10, 10, 330, 100)

        self.date_label = QLabel(self.datetime_group, text="Date:")
        self.date_label.setGeometry(10, 20, 60, 28)
        self.date_label.setObjectName("default_label")
        self.date_label.setFont(Window.font_bold_14)

        self.time_label = QLabel(self.datetime_group, text="Time:")
        self.time_label.setGeometry(10, 60, 60, 28)
        self.time_label.setObjectName("default_label")
        self.time_label.setFont(Window.font_bold_14)

        self.day_month_separator = QLabel(self.datetime_group, text=".")
        self.day_month_separator.move(145, 22)
        self.day_month_separator.setObjectName("time_label")
        self.day_month_separator.setFont(Window.font_bold_15)

        self.month_year_separator = QLabel(self.datetime_group, text=".")
        self.month_year_separator.move(220, 22)
        self.month_year_separator.setObjectName("time_label")
        self.month_year_separator.setFont(Window.font_bold_15)

        self.hour_minute_separator = QLabel(self.datetime_group, text=":")
        self.hour_minute_separator.move(145, 60)
        self.hour_minute_separator.setObjectName("time_label")
        self.hour_minute_separator.setFont(Window.font_bold_15)

        self.minute_second_separator = QLabel(self.datetime_group, text=":")
        self.minute_second_separator.move(220, 60)
        self.minute_second_separator.setObjectName("time_label")
        self.minute_second_separator.setFont(Window.font_bold_15)

        self.day_spin_box = PickSpinbox(self.datetime_group)
        self.day_spin_box.move(80, 20)
        self.day_spin_box.setRange(1, 31)
        self.day_spin_box.setValue(self.now.day)

        self.month_spin_box = PickSpinbox(self.datetime_group)
        self.month_spin_box.move(155, 20)
        self.month_spin_box.setRange(1, 12)
        self.month_spin_box.setValue(self.now.month)

        self.year_spin_box = PickSpinbox(self.datetime_group)
        self.year_spin_box.move(230, 20)
        self.year_spin_box.setRange(1, 9999)
        self.year_spin_box.setValue(self.now.year)

        self.hours_spin_box = PickSpinbox(self.datetime_group)
        self.hours_spin_box.move(80, 60)
        self.hours_spin_box.setRange(0, 23)
        self.hours_spin_box.setValue(self.now.hour)

        self.minutes_spin_box = PickSpinbox(self.datetime_group)
        self.minutes_spin_box.move(155, 60)
        self.minutes_spin_box.setRange(0, 59)
        self.minutes_spin_box.setValue(self.now.minute)

        self.seconds_spin_box = PickSpinbox(self.datetime_group)
        self.seconds_spin_box.move(230, 60)
        self.seconds_spin_box.setRange(0, 59)
        self.seconds_spin_box.setValue(self.now.second)

        self.write_xml_box = QCheckBox(self)
        self.write_xml_box.move(120, 130)
        self.write_xml_box.setText("Write XML File")
        self.write_xml_box.setChecked(True)
        self.write_xml_box.setFont(Window.font_normal_10)

        self.confirm_date_button = QPushButton(self)
        self.confirm_date_button.setGeometry(250, 120, 100, 32)
        self.confirm_date_button.setText("CONFIRM")
        self.confirm_date_button.setFont(Window.font_bold_10)
        self.confirm_date_button.setObjectName("secondary_button")
        self.confirm_date_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.confirm_date_button.clicked.connect(self.confirm_date)

    def confirm_date(self):
        Window.base_time = datetime.datetime(self.year_spin_box.value(), self.month_spin_box.value(),
                                             self.day_spin_box.value(), self.hours_spin_box.value(),
                                             self.minutes_spin_box.value(), self.seconds_spin_box.value())
        if self.write_xml_box.isChecked():
            for Window.video_index in range(len(Window.videopath_list)):
                meta_data_video = cv2.VideoCapture(Window.videopath_list[Window.video_index])

                Window.length = int(meta_data_video.get(cv2.CAP_PROP_FRAME_COUNT))
                Window.Fps = int(meta_data_video.get(cv2.CAP_PROP_FPS))
                Window.Height = int(meta_data_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                Window.Width = int(meta_data_video.get(cv2.CAP_PROP_FRAME_WIDTH))

                non_realtime_meta = Et.Element('NonRealTimeMeta')
                duration = Et.SubElement(non_realtime_meta, 'Duration')
                duration.set('value', str(Window.length))
                creation_date = Et.SubElement(non_realtime_meta, 'CreationDate')
                creation_date.set('value',
                                  '%04d' % self.year_spin_box.value() + '-' + '%02d' % self.month_spin_box.value() +
                                  '-' + '%02d' % self.day_spin_box.value() + 'T' +
                                  '%02d' % self.hours_spin_box.value() + ':' + '%02d' % self.minutes_spin_box.value() +
                                  ':' + '%02d' % self.seconds_spin_box.value() + '+1:00')
                video_format = Et.SubElement(non_realtime_meta, 'VideoFormat')
                video_frame = Et.SubElement(video_format, 'VideoFrame')
                video_frame.set('captureFps', str(Window.Fps))
                video_layout = Et.SubElement(video_format, 'VideoLayout')
                video_layout.set('pixel', str(Window.Width))
                video_layout.set('numOfVerticalLine', str(Window.Height))

                xml_data = Et.tostring(non_realtime_meta, "unicode")

                self.write_xml_path = QFileDialog.getSaveFileName(
                    self,
                    "Select a directory to save the generated XML file.",
                    f"{Window.videopath_list[Window.video_index][:-4]}.XML",
                    "XML Files (*.xml)")
                self.write_xml_path = self.write_xml_path[0]

                if self.write_xml_path != "":
                    with open(self.write_xml_path, "w") as f:
                        f.write(xml_data)

        self.accept()


class SettingSpinboxPair(QHBoxLayout):
    def __init__(self, parent, label, value):
        QHBoxLayout.__init__(self, parent)

        self.label = QLabel()
        self.label.setText(label)

        self.spinbox = QSpinBox()
        self.spinbox.setMaximumWidth(60)
        self.spinbox.setRange(0, 10000)
        self.spinbox.setValue(value)

        self.addWidget(self.label)
        self.addWidget(self.spinbox)

    def change_value(self, value):
        self.spinbox.setValue(value)

    def get_value(self):
        return self.spinbox.value()


class SettingInputPair(QHBoxLayout):
    def __init__(self, parent, label, text):
        QHBoxLayout.__init__(self, parent)

        self.label = QLabel()
        self.label.setText(label)

        self.text_field = QLineEdit(text)
        self.text_field.setMaximumWidth(100)
        self.text_field.setMaxLength(14)

        self.addWidget(self.label)
        self.addWidget(self.text_field)

    def change_value(self, text):
        self.text_field.setText(text)

    def get_value(self):
        return self.text_field.text()


class SettingResolutionPair(QHBoxLayout):
    def __init__(self, parent, label, index):
        QHBoxLayout.__init__(self, parent)

        self.label = QLabel()
        self.label.setText(label)

        self.combobox = QComboBox()
        self.combobox.setMaximumWidth(140)
        self.combobox.insertItem(0, "VGA (640x480)", (640, 480))
        self.combobox.insertItem(1, "qHD (960x540)", (960, 540))
        self.combobox.insertItem(2, "HD (1280x720)", (1280, 720))
        self.combobox.insertItem(3, "Full HD (1920x1080)", (1920, 1080))
        self.combobox.insertItem(4, "QHD (2560x1440)", (2560, 1440))
        self.combobox.insertItem(5, "Ultra HD (3840x2160)", (3840, 2160))
        self.combobox.setCurrentIndex(index)

        self.addWidget(self.label)
        self.addWidget(self.combobox)

    def change_value(self, data):
        index = self.combobox.findText(str(data[0]), Qt.MatchContains)
        self.combobox.setCurrentIndex(index)

    def get_value(self):
        return self.combobox.currentData(Qt.UserRole)


class SettingDoubleSpinboxPair(QHBoxLayout):
    def __init__(self, parent, label, value):
        QHBoxLayout.__init__(self, parent)

        self.label = QLabel()
        self.label.setText(label)

        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMaximumWidth(60)
        self.spinbox.setRange(0, 10000)
        self.spinbox.setValue(value)
        self.spinbox.setSingleStep(0.01)

        self.addWidget(self.label)
        self.addWidget(self.spinbox)

    def change_value(self, value):
        self.spinbox.setValue(value)

    def get_value(self):
        return self.spinbox.value()


class SettingsWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.resize(500, 700)

        self.app_icon = QIcon()
        self.app_icon.addPixmap(QPixmap("files/logo.ico"), QIcon.Normal, QIcon.Off)

        self.setWindowTitle("VAMOS+ - Settings")
        self.setWindowIcon(self.app_icon)

        self.init_ui()

    def init_ui(self):
        self.tab_widget = QTabWidget(self)
        self.tab_widget.resize(500, 700)

        self.values_tab = QWidget(self)
        self.values_tab.setVisible(False)
        self.tab_widget.addTab(self.values_tab, "Values")

        self.v_layout = QVBoxLayout(self.values_tab)
        self.v_layout.setContentsMargins(20, 20, 20, 0)

        self.resolution_label = QLabel(self)
        self.resolution_label.setText("These settings are dependent on the resolution of the video.\n"
                                      "The values below are used for Full HD (1920 x 1080).")
        self.resolution_label.setMaximumHeight(50)

        self.blur = SettingSpinboxPair(self.values_tab, "Blur [px]", 0)
        self.x_grid = SettingSpinboxPair(self.values_tab, "Horizontal Grid", 0)
        self.y_grid = SettingSpinboxPair(self.values_tab, "Vertical Grid", 0)
        self.thresh_value = SettingSpinboxPair(self.values_tab, "Threshold", 0)
        self.thresh_max_brightness = SettingSpinboxPair(self.values_tab, "Threshold max. brightness", 0)
        self.dilate = SettingSpinboxPair(self.values_tab, "Dilation [px]", 0)
        self.max_meteors = SettingSpinboxPair(self.values_tab, "Max. Signals before reference frame reset", 0)
        self.min_area = SettingSpinboxPair(self.values_tab, "Min. Area [px]", 0)
        self.max_area = SettingSpinboxPair(self.values_tab, "Max. Area [px]", 0)
        self.signal_label = SettingInputPair(self.values_tab, "Detection Label", "")
        self.sort_out_area_difference = SettingSpinboxPair(self.values_tab, "Max. difference between 2 frames [px]", 0)
        self.max_length = SettingDoubleSpinboxPair(self.values_tab, "Max. Length [s]", 0)
        self.min_length = SettingDoubleSpinboxPair(self.values_tab, "Min. Length [s]", 0)
        self.resolution_to_write = SettingResolutionPair(self.values_tab, "Resolution of written images", 0)
        self.max_distance = SettingSpinboxPair(self.values_tab, "Max. distance [px]", 0)
        self.max_frames = SettingSpinboxPair(self.values_tab, "Max. frames", 0)
        self.delete_threshold = SettingSpinboxPair(self.values_tab, "Max. number of marked frames", 0)
        self.delete_percentage = SettingDoubleSpinboxPair(self.values_tab, "Max. ratio of marked frames", 0)

        self.reset_layout = QHBoxLayout()
        self.reset_spacer = QSpacerItem(350, 10)
        self.reset_button = QPushButton("Reset to defaults")

        self.button_layout = QHBoxLayout()
        self.spacer = QSpacerItem(200, 10)
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.apply_button = QPushButton("Apply")

        self.reset_layout.addWidget(self.reset_button)
        self.reset_layout.addItem(self.reset_spacer)

        self.button_layout.addItem(self.spacer)
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.apply_button)

        self.v_layout.addWidget(self.resolution_label)
        self.v_layout.addLayout(self.reset_layout)
        self.v_layout.addLayout(self.blur)
        self.v_layout.addLayout(self.x_grid)
        self.v_layout.addLayout(self.y_grid)
        self.v_layout.addLayout(self.thresh_value)
        self.v_layout.addLayout(self.thresh_max_brightness)
        self.v_layout.addLayout(self.dilate)
        self.v_layout.addLayout(self.max_meteors)
        self.v_layout.addLayout(self.min_area)
        self.v_layout.addLayout(self.max_area)
        self.v_layout.addLayout(self.signal_label)
        self.v_layout.addLayout(self.sort_out_area_difference)
        self.v_layout.addLayout(self.max_length)
        self.v_layout.addLayout(self.min_length)
        self.v_layout.addLayout(self.resolution_to_write)
        self.v_layout.addLayout(self.max_distance)
        self.v_layout.addLayout(self.max_frames)
        self.v_layout.addLayout(self.delete_threshold)
        self.v_layout.addLayout(self.delete_percentage)
        self.v_layout.addLayout(self.button_layout)

        self.setup_values()

        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.ok_button.clicked.connect(self.ok_pressed)
        self.apply_button.clicked.connect(self.apply_pressed)
        self.cancel_button.clicked.connect(self.close)

    def reset_to_defaults(self):
        reset_continue = QMessageBox.question(Window, "Do you want to reset?",
                                              "Are you sure that you want to reset the values to defaults?",
                                              QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reset_continue == QMessageBox.Yes:
            self.blur.change_value(20)
            self.x_grid.change_value(8)
            self.y_grid.change_value(5)
            self.thresh_value.change_value(20)
            self.thresh_max_brightness.change_value(255)
            self.dilate.change_value(2)
            self.max_meteors.change_value(5)
            self.min_area.change_value(60)
            self.max_area.change_value(4000)
            self.signal_label.change_value("Detection")
            self.sort_out_area_difference.change_value(4)
            self.max_length.change_value(10)
            self.min_length.change_value(0.04)
            self.resolution_to_write.change_value([960, 540])
            self.max_distance.change_value(100)
            self.max_frames.change_value(3)
            self.delete_threshold.change_value(10)
            self.delete_percentage.change_value(0.25)

            set_defaults_success_message = QMessageBox(icon=QMessageBox.Information,
                                                       text="Successfully reset to defaults!")
            set_defaults_success_message.setWindowTitle("Info")
            set_defaults_success_message.exec_()

    def apply_pressed(self):
        if self.blur.get_value() % 2 == 1:
            no_odd_number = QMessageBox(icon=QMessageBox.Critical,
                                        text="For the blur value, no odd numbers are allowed.")
            no_odd_number.setWindowTitle("No odd numbers allowed")
            no_odd_number.exec_()
            return False
        settings_list = [
            self.blur.get_value(),
            self.x_grid.get_value(),
            self.y_grid.get_value(),
            self.thresh_value.get_value(),
            self.thresh_max_brightness.get_value(),
            self.dilate.get_value(),
            self.max_meteors.get_value(),
            self.min_area.get_value(),
            self.max_area.get_value(),
            self.signal_label.get_value(),
            self.sort_out_area_difference.get_value(),
            self.max_length.get_value(),
            self.min_length.get_value(),
            self.resolution_to_write.get_value(),
            self.max_distance.get_value(),
            self.max_frames.get_value(),
            self.delete_threshold.get_value(),
            self.delete_percentage.get_value()
        ]
        with open("files/settings.data", "w") as settings_file:
            settings_file.write(json.dumps(settings_list))
        return True

    def ok_pressed(self):
        if self.apply_pressed():
            self.close()

    def setup_values(self):
        with open("files/settings.data", "r") as settings_file:
            settings_list = json.loads(settings_file.read())
            self.blur.change_value(settings_list[0])
            self.x_grid.change_value(settings_list[1])
            self.y_grid.change_value(settings_list[2])
            self.thresh_value.change_value(settings_list[3])
            self.thresh_max_brightness.change_value(settings_list[4])
            self.dilate.change_value(settings_list[5])
            self.max_meteors.change_value(settings_list[6])
            self.min_area.change_value(settings_list[7])
            self.max_area.change_value(settings_list[8])
            self.signal_label.change_value(settings_list[9])
            self.sort_out_area_difference.change_value(settings_list[10])
            self.max_length.change_value(settings_list[11])
            self.min_length.change_value(settings_list[12])
            self.resolution_to_write.change_value(settings_list[13])
            self.max_distance.change_value(settings_list[14])
            self.max_frames.change_value(settings_list[15])
            self.delete_threshold.change_value(settings_list[16])
            self.delete_percentage.change_value(settings_list[17])


class TableModel(QAbstractTableModel):
    def __init__(self, data, header_labels):
        super(TableModel, self).__init__()
        self._data = data
        self.header_labels = header_labels

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        return len(self._data)

    def columnCount(self, index):
        try:
            return len(self._data[0])
        except IndexError:
            return 0

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.header_labels[section]
        return QAbstractTableModel.headerData(self, section, orientation, role)

    def removeRow(self, position, parent=QModelIndex(), *args, **kwargs):
        self.beginRemoveRows(parent, position, position)
        del self._data[position]
        self.endRemoveRows()
        return True


class MeteorTableView(QTableView):
    def __init__(self, results_window):
        super(MeteorTableView, self).__init__()
        self.results_window = results_window
        self.len_mul = self.results_window.Height_list[0] // 1080
        self.ar_mul = self.len_mul ** 2

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        deleteSelectedAction = QAction("Delete Selected", self)
        deleteSelectedAction.triggered.connect(self.delete_selected)
        deleteSimilarAction = QAction("Delete Similar", self)
        deleteSimilarAction.triggered.connect(self.delete_similar)
        self.menu.addAction(deleteSelectedAction)
        self.menu.addAction(deleteSimilarAction)
        self.menu.popup(QCursor.pos())

    def delete_selected(self):
        selections = self.selectedIndexes()
        for index_correction, row in enumerate(sorted(set([selection.row() for selection in selections]))):
            self.delete_meteor(row - index_correction)
        self.clearSelection()

    def delete_meteor(self, index):
        meteor_id = self.model().index(index, 0).data()
        del self.results_window.meteors[meteor_id]
        self.results_window.meteor_data_model.removeRow(index)

    def delete_similar(self):
        row = self.selectedIndexes()[0].row()
        previous_meteor_id = self.model().index(row, 0).data()
        similar_meteors = [row]
        exception_count = 0
        for index in range(row + 1, len(self.results_window.meteors)):
            meteor_id = self.model().index(index, 0).data()
            if check_pos(self.results_window.meteors[meteor_id]["position"],
                         self.results_window.meteors[previous_meteor_id]["position"], 75 * self.len_mul) and \
                    abs(self.results_window.meteors[meteor_id]["area"] -
                        self.results_window.meteors[previous_meteor_id]["area"]) <= 100 * self.ar_mul:
                similar_meteors.append(index)
                previous_meteor_id = meteor_id
                exception_count = 0
            else:
                exception_count += 1
                if exception_count > 3:
                    exception_count = 0
                    break
        for index_correction, index in enumerate(similar_meteors):
            print(index)
            self.delete_meteor(index - index_correction)
        self.clearSelection()


class CustomGraphicsView(QGraphicsView):
    def __init__(self):
        QGraphicsView.__init__(self)

        self.coordinates = [0, 0]
        self.paint = False

    def draw(self, coordinates):
        self.coordinates = coordinates
        self.paint = True

    def paintEvent(self, event):
        QGraphicsView.paintEvent(self, event)
        if self.paint:
            painter = QPainter(self.viewport())
            painter.begin(self)
            painter.setPen(Qt.lightGray)
            painter.drawRect(int((self.coordinates[0]) - 50), int(self.coordinates[1] - 50), 100, 100)
            painter.end()


class ResultsWindow(QWidget):
    def __init__(self, vamos_filepath):
        QWidget.__init__(self)

        self.app_icon = QIcon()
        self.app_icon.addPixmap(QPixmap("files/logo.ico"), QIcon.Normal, QIcon.Off)
        self.volume_icon = QIcon()
        self.volume_icon.addPixmap(QPixmap("files/volume.png"), QIcon.Normal, QIcon.Off)
        self.volume_muted_icon = QIcon()
        self.volume_muted_icon.addPixmap(QPixmap("files/volume_mute.png"), QIcon.Normal, QIcon.Off)
        self.play_icon = QIcon()
        self.play_icon.addPixmap(QPixmap("files/play.png"), QIcon.Normal, QIcon.Off)
        self.pause_icon = QIcon()
        self.pause_icon.addPixmap(QPixmap("files/pause.png"), QIcon.Normal, QIcon.Off)
        self.loop_icon = QIcon()
        self.loop_icon.addPixmap(QPixmap("files/loop.png"), QIcon.Normal, QIcon.Off)
        self.loop_disabled_icon = QIcon()
        self.loop_disabled_icon.addPixmap(QPixmap("files/loop_disabled.png"), QIcon.Normal, QIcon.Off)
        self.square_icon = QIcon()
        self.square_icon.addPixmap(QPixmap("files/square.png"), QIcon.Normal, QIcon.Off)
        self.square_disabled_icon = QIcon()
        self.square_disabled_icon.addPixmap(QPixmap("files/square_disabled.png"), QIcon.Normal, QIcon.Off)

        self.vamos_filepath = vamos_filepath

        self.setObjectName("default_widget")
        self.setWindowTitle(f"VAMOS+ - {self.vamos_filepath}")
        self.setWindowIcon(self.app_icon)
        self.setGeometry(350, 100, 900, 500)

        self.init_ui()

        self.showMaximized()

    def init_ui(self):
        self.font_big = QFont()
        self.font_big.setPointSize(11)

        self.meta_data_table = QTableView(self)

        self.get_vamos_data()

        self.meta_data_table_data = []

        for i in range(len(self.videopath_list)):
            self.meta_data_table_data.append(
                [self.videopath_list[i], self.xmlpath_list[i], str(self.base_time_list[i]), self.length_list[i],
                 self.Fps_list[i], f"{self.Width_list[i]} x {self.Height_list[i]}"])

        self.meta_data_model = TableModel(self.meta_data_table_data,
                                          ['Videopath', 'XML-Path', 'Video start', 'Duration', 'FPS', 'Resolution'])
        self.meta_data_table.setModel(self.meta_data_model)
        self.meta_data_table.setColumnWidth(0, 400)
        self.meta_data_table.setColumnWidth(1, 280)
        self.meta_data_table.setColumnWidth(2, 150)
        self.meta_data_table.setColumnWidth(3, 65)
        self.meta_data_table.setColumnWidth(4, 60)
        self.meta_data_table.setColumnWidth(5, 100)

        self.meta_data_table.clicked.connect(self.meta_cell_clicked)

        self.meteor_data_table = MeteorTableView(self)
        self.meteor_data_table.setMinimumWidth(1000)

        self.meteor_data_table_data = []

        for meteor_id in self.meteors:
            meteor = self.meteors[meteor_id]
            self.meteor_data_table_data.append([
                meteor_id,
                meteor['VideoID'],
                f"{meteor['position'][0]}, {meteor['position'][1]}",
                str(meteor['frames'])[1:-1],
                datetime.time(*meteor['beginning'][0]).strftime("%H:%M:%S.%f")[:-4],
                datetime.time(*meteor['end'][0]).strftime("%H:%M:%S.%f")[:-4],
                datetime.time(*meteor['beginning'][1]).strftime("%H:%M:%S.%f")[:-4],
                datetime.time(*meteor['end'][1]).strftime("%H:%M:%S.%f")[:-4],
                str(meteor['duration']) + " frames",
                str(meteor['area']) + " px",
                datetime.date(*meteor['date']).strftime("%d.%m.%Y")
            ])

        self.meteor_data_model = TableModel(self.meteor_data_table_data, ['MeteorID',
                                                                          'VideoID',
                                                                          'Position',
                                                                          'Frames',
                                                                          'Beginning CET',
                                                                          'End CET',
                                                                          'Beginning Video',
                                                                          'End Video',
                                                                          'Duration',
                                                                          'max. Area',
                                                                          'Date'])
        self.meteor_data_table.setModel(self.meteor_data_model)
        self.meteor_data_table.setColumnWidth(0, 85)
        self.meteor_data_table.setColumnWidth(1, 65)
        self.meteor_data_table.setColumnWidth(2, 70)
        self.meteor_data_table.setColumnWidth(3, 100)
        self.meteor_data_table.setColumnWidth(4, 85)
        self.meteor_data_table.setColumnWidth(5, 85)
        self.meteor_data_table.setColumnWidth(6, 100)
        self.meteor_data_table.setColumnWidth(7, 85)
        self.meteor_data_table.setColumnWidth(8, 80)
        self.meteor_data_table.setColumnWidth(9, 70)
        self.meteor_data_table.setColumnWidth(10, 80)

        self.meteor_data_table.clicked.connect(self.meteor_cell_clicked)

        self.project_info_box = QGroupBox()
        self.project_info_box.setTitle("Project information")
        self.project_info_box.setFlat(True)
        self.project_info_box.setFixedHeight(80)

        self.folderpath_label = QLabel(self.project_info_box)
        self.folderpath_label.move(10, 20)
        self.folderpath_label.setMinimumWidth(500)
        self.folderpath_label.setText("Folderpath: \n" + self.folderpath)
        self.folderpath_label.setObjectName("default_label")
        self.folderpath_label.setFont(self.font_big)

        self.generate_spreadsheet_button = QPushButton("GENERATE SPREADSHEET")
        self.generate_spreadsheet_button.setObjectName("secondary_button_wide")
        self.generate_spreadsheet_button.setFont(Window.font_bold_10)
        self.generate_spreadsheet_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.save_file_button = QPushButton("SAVE FILE")
        self.save_file_button.setObjectName("secondary_button")
        self.save_file_button.setFont(Window.font_bold_10)
        self.save_file_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.video_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.videopath_list[0])))
        self.video_player.play()
        self.video_player.pause()

        self.media_index = 0

        # self.video_widget = QVideoWidget(self)
        self.graphics_view = CustomGraphicsView()
        self.graphics_scene = QGraphicsScene(self.graphics_view)
        self.video_item = QGraphicsVideoItem()
        self.video_item.setSize(QSizeF(self.graphics_view.size().width(), self.graphics_view.size().width() * (9 / 16)))
        self.graphics_view.setScene(self.graphics_scene)
        self.graphics_scene.addItem(self.video_item)
        self.video_player.setVideoOutput(self.video_item)

        self.video_name_label = QLabel()
        self.video_name_label.setText(os.path.basename(self.video_player.currentMedia().canonicalUrl().toString()))
        self.video_name_label.setObjectName("default_label")
        self.video_name_label.setMaximumHeight(25)
        self.video_name_label.setFont(Window.font_bold_14)

        self.mute_button = QPushButton(self)
        self.mute_button.setIcon(self.volume_icon)
        self.mute_button.setObjectName("video_button")
        self.play_button = QPushButton(self)
        self.play_button.setIcon(self.play_icon)
        self.play_button.setObjectName("video_button")
        self.loop_button = QPushButton(self)
        self.loop_button.setIcon(self.loop_disabled_icon)
        self.loop_button.setObjectName("video_button")
        self.loop = False
        self.square_button = QPushButton(self)
        self.square_button.setIcon(self.square_disabled_icon)
        self.square_button.setObjectName("video_button")

        self.time_label = QLabel(self)
        self.time_label.setText("00:00:00")
        self.time_label.setMaximumSize(QSize(60, 12))
        self.time_label.setObjectName("default_label")
        self.time_label.setFont(Window.font_normal_10)
        self.frame_label = QLabel(self)
        self.frame_label.setText("0")
        self.frame_label.setMaximumSize(QSize(60, 12))
        self.frame_label.setObjectName("default_label")
        self.frame_label.setFont(Window.font_normal_10)
        self.video_time = datetime.time(0, 0, 0)

        self.video_slider = QSlider(Qt.Horizontal, self)

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignCenter)
        self.control_layout = QHBoxLayout(self)
        self.video_layout = QVBoxLayout(self)
        self.data_layout = QSplitter(self)
        self.data_layout.setOrientation(Qt.Vertical)

        self.control_layout.addWidget(self.time_label)
        self.control_layout.addWidget(self.play_button)
        self.control_layout.addWidget(self.video_slider)
        self.control_layout.addWidget(self.mute_button)
        self.control_layout.addWidget(self.loop_button)
        self.control_layout.addWidget(self.square_button)
        self.control_layout.addWidget(self.frame_label)

        self.data_layout.addWidget(self.meta_data_table)
        self.data_layout.addWidget(self.meteor_data_table)

        self.main_layout.addLayout(self.video_layout)
        self.main_layout.addWidget(self.data_layout)

        self.video_layout.addWidget(self.project_info_box)
        self.video_layout.addWidget(self.generate_spreadsheet_button)
        self.video_layout.addWidget(self.save_file_button)
        self.video_layout.addWidget(self.graphics_view)
        self.video_layout.addWidget(self.video_name_label)
        self.video_layout.addLayout(self.control_layout)

        self.mute_button.clicked.connect(self.toggle_muted)
        self.play_button.clicked.connect(self.toggle_play)
        self.loop_button.clicked.connect(self.toggle_loop)
        self.square_button.clicked.connect(self.toggle_square)
        self.generate_spreadsheet_button.clicked.connect(self.generate_spreadsheet)
        self.save_file_button.clicked.connect(self.save_file)

        self.square_button.setToolTip("Toggle the square shown whereever the meteor signal occured.")
        self.generate_spreadsheet_button.setToolTip(
            "Generate a spreadsheet with all data shown in the meteor data table.")

        self.video_player.mediaStatusChanged.connect(self.handle_media_status)
        self.video_player.positionChanged.connect(self.position_changed)
        self.video_player.durationChanged.connect(self.duration_changed)
        self.video_player.mediaChanged.connect(self.media_changed)

        self.video_slider.sliderMoved.connect(self.set_position)

    def paintEvent(self, event):
        self.video_item.setSize(QSizeF(self.graphics_view.size().width(), self.graphics_view.size().width() * (9 / 16)))

    def get_vamos_data(self):
        self.path = self.vamos_filepath
        with open(self.path, "r") as f:
            self.data = f.read().split(sep="\n")
            self.videopath_list, self.xmlpath_list, self.folderpath = json.loads(self.data[0])
            self.base_times = json.loads(self.data[1])
            self.base_time_list = []
            for base_time in self.base_times:
                self.base_time_list.append(datetime.datetime(*base_time))
            self.length_list = json.loads(self.data[2])
            self.Fps_list = json.loads(self.data[3])
            self.Width_list, self.Height_list = json.loads(self.data[4])
            self.meteors = json.loads(self.data[5])

    def generate_spreadsheet(self):
        spreadsheet_path = QFileDialog.getSaveFileName(
            parent=self,
            filter="Spreadsheet Files (*.xlsx *.xls *.ods)",
            directory=self.folderpath
        )[0]

        if spreadsheet_path != "":
            wb = load_workbook("files/Results_template.xlsx")

            sheet = wb.active
            sheet.title = "VAMOS+"

            for row, meteor_id in enumerate(self.meteors):
                meteor = self.meteors[meteor_id]
                sheet.append((
                    meteor_id,
                    meteor['VideoID'],
                    f"{meteor['position'][0]}, {meteor['position'][1]}",
                    str(meteor['frames'])[1:-1],
                    datetime.time(*meteor['beginning'][0]).strftime("%H:%M:%S.%f")[:-4],
                    datetime.time(*meteor['end'][0]).strftime("%H:%M:%S.%f")[:-4],
                    datetime.time(*meteor['beginning'][1]).strftime("%H:%M:%S.%f")[:-4],
                    datetime.time(*meteor['end'][1]).strftime("%H:%M:%S.%f")[:-4],
                    round(meteor['duration'] / self.Fps_list[0], 2),
                    meteor['area'],
                    datetime.date(*meteor['date']).strftime("%d.%m.%Y")
                ))

            wb.save(spreadsheet_path)

    def save_file(self):
        vamos_filepath = QFileDialog.getSaveFileName(self,
                                                     "Select a directory to save the VAMOS file in",
                                                     self.path,
                                                     "VAMOS Files (*.vamos)")[0]
        if vamos_filepath != "":
            with open(vamos_filepath, "w") as f:
                f.write(
                    json.dumps([self.videopath_list, self.xmlpath_list, self.folderpath]) + "\n" +
                    json.dumps(self.base_times) + "\n" +
                    json.dumps(self.length_list) + "\n" +
                    json.dumps(self.Fps_list) + "\n" +
                    json.dumps([self.Width_list, self.Height_list]) + "\n" +
                    json.dumps(self.meteors)
                )

    def toggle_muted(self):
        if self.video_player.isMuted():
            self.video_player.setMuted(False)
            self.mute_button.setIcon(self.volume_icon)
        else:
            self.video_player.setMuted(True)
            self.mute_button.setIcon(self.volume_muted_icon)

    def toggle_play(self):
        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.pause()
            self.play_button.setIcon(self.play_icon)
        else:
            self.video_player.play()
            self.play_button.setIcon(self.pause_icon)

    def toggle_loop(self):
        if self.loop:
            self.loop_button.setIcon(self.loop_disabled_icon)
            self.loop = False
        else:
            self.loop_button.setIcon(self.loop_icon)
            self.loop = True

    def toggle_square(self):
        if self.graphics_view.paint:
            self.square_button.setIcon(self.square_disabled_icon)
            self.graphics_view.paint = False
        else:
            self.square_button.setIcon(self.square_icon)
            self.graphics_view.paint = True

    def closeEvent(self, event):
        # Make sure the video stops when the window closes
        if self.video_player.state() == QMediaPlayer.PlayingState:
            self.video_player.stop()
        event.accept()

    def handle_media_status(self):
        if self.video_player.mediaStatus() == QMediaPlayer.EndOfMedia:
            if self.loop:
                self.video_player.play()
                self.play_button.setIcon(self.pause_icon)
            elif self.media_index < len(self.videopath_list) - 1:
                self.media_index += 1
                self.video_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.videopath_list[self.media_index])))
                self.video_player.play()
                self.play_button.setIcon(self.pause_icon)
            else:
                self.video_player.pause()
                self.play_button.setIcon(self.play_icon)
            self.video_player.setPosition(1)

    def position_changed(self, position):
        self.video_slider.setValue(position)
        self.video_time = datetime.timedelta(milliseconds=position)
        self.time_label.setText(str(self.video_time)[:7])
        self.frame_label.setText(str(int(self.video_time.total_seconds() * self.Fps_list[self.media_index])))

    def duration_changed(self, duration):
        self.video_slider.setRange(0, duration)

    def media_changed(self, media):
        self.video_name_label.setText(os.path.basename(media.canonicalUrl().toString()))

    def set_position(self, position):
        self.video_player.setPosition(int(position))

    def meta_cell_clicked(self):
        cell_index = self.meta_data_table.selectedIndexes()[0]
        if str(cell_index.data())[-4:].lower() == ".mp4":
            self.video_player.setMedia(
                QMediaContent(QUrl.fromLocalFile(cell_index.data())))
            self.video_player.play()
            self.play_button.setIcon(self.pause_icon)

            self.media_index = cell_index.row()

    def meteor_cell_clicked(self):
        cell_index = self.meteor_data_table.selectedIndexes()[0]
        model = self.meteor_data_table.model()
        meteor_index = cell_index.row()
        for i, video in enumerate(self.videopath_list):
            if os.path.basename(video)[:-4] == model.index(meteor_index, 1).data():
                self.video_player.setMedia(
                    QMediaContent(QUrl.fromLocalFile(video)))
                self.video_player.play()
                self.video_player.setPosition(int((int(model.index(meteor_index, 3).data().split(",")[0]) - 3) * (1000 / self.Fps_list[i])))
                self.play_button.setIcon(self.pause_icon)

                self.media_index = i
                divider = self.Width_list[i] / self.graphics_view.size().width()
                coordinates = [
                    int(model.index(meteor_index, 2).data().split(",")[0]) // divider,
                    int(model.index(meteor_index, 2).data().split(",")[1]) // divider + (
                                self.graphics_view.height() - self.video_item.size().height()) // 2
                ]
                self.square_button.setIcon(self.square_icon)
                self.graphics_view.paint = True
                self.graphics_view.draw(coordinates)


class AnalysationWindow(QMainWindow):
    def __init__(self):
        super(AnalysationWindow, self).__init__()

        # Define fonts
        # roboto_light = QFontDatabase.addApplicationFont("files/Roboto-Light.ttf")
        self.default_font = QFont("Roboto Light", 9)
        self.font_bold_9 = QFont("Roboto Light", 9)
        self.font_bold_9.setBold(True)
        self.font_bold_10 = QFont("Roboto Light", 10)
        self.font_bold_10.setBold(True)
        self.font_bold_14 = QFont("Roboto Medium", 14)
        self.font_bold_14.setBold(True)
        self.font_normal_10 = QFont("Roboto Light", 10)
        self.font_bold_15 = QFont("Poetsen One", 15)
        self.font_bold_15.setBold(True)

        # define icons
        self.app_icon = QIcon()
        self.app_icon.addPixmap(QPixmap("files/logo.ico"), QIcon.Normal, QIcon.Off)
        self.trash_icon = QIcon()
        self.trash_icon.addPixmap(QPixmap("files/trash_icon.png"), QIcon.Normal, QIcon.Off)
        self.analyse_icon = QIcon()
        self.analyse_icon.addPixmap(QPixmap("files/analyse_icon.png"), QIcon.Normal, QIcon.Off)

        # define movies
        self.loading_animation = QMovie("files/loading.gif")
        self.loading_animation.setScaledSize(QSize(32, 32))

        self.unsaved_changes = False
        self.was_successful = False
        self.broke_frame = 0

        self.resize(1000, 600)
        self.setFont(self.default_font)
        self.setWindowTitle("VAMOS+ - Video-Assisted Meteor Observation System")
        self.setWindowIcon(self.app_icon)
        self.setObjectName("AnalysationWindow")
        self.init_ui()

        if len(sys.argv) > 1:
            if os.path.splitext(sys.argv[1])[1] == ".vamos":
                self.vamos_file_path = sys.argv[1]
            else:
                no_valid_vamos_file = QMessageBox(icon=QMessageBox.Critical, text="The file you are trying to open is "
                                                                                  "not a valid .vamos file.")
                no_valid_vamos_file.setWindowTitle("XML not found")
                no_valid_vamos_file.exec_()
        else:
            self.vamos_file_path = ""

    def init_ui(self):
        # setup the main widget
        self.centralwidget = QWidget(self)

        # Setup the logo
        self.vamos_title_image = QLabel(self.centralwidget)
        self.vamos_title_image.setGeometry(10, 20, 400, 100)
        self.vamos_title_image.setPixmap(QPixmap("files/vamos_plus_logo_white.png"))
        self.vamos_title_image.setScaledContents(True)

        # Thumbnail section
        self.video_thumb_label = QLabel(self.centralwidget)
        self.video_thumb_label.move(260, 170)
        self.video_thumb_label.setText("Video preview:")
        self.video_thumb_label.setObjectName("default_label")
        self.video_thumb_label.setFont(self.font_bold_10)

        self.video_thumb = QLabel(self.centralwidget)
        self.video_thumb.move(405, 125)
        self.video_thumb.resize(192, 108)
        self.video_thumb.setPixmap(QPixmap("files/default_thumbnail.png"))
        self.video_thumb.setScaledContents(True)
        self.video_thumb.setObjectName("video_thumb")

        # File selection section
        self.file_selection_widget = QWidget(self.centralwidget)
        self.file_selection_widget.setGeometry(20, 240, 850, 200)
        self.file_selection_grid = QGridLayout(self.file_selection_widget)
        self.file_selection_grid.setContentsMargins(0, 0, 0, 0)

        self.video_selection_status = QLabel(self.file_selection_widget)
        self.video_selection_status.setObjectName("selection_status")
        self.video_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
        self.xml_selection_status = QLabel(self.file_selection_widget)
        self.xml_selection_status.setObjectName("selection_status")
        self.xml_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
        self.folder_selection_status = QLabel(self.file_selection_widget)
        self.folder_selection_status.setObjectName("selection_status")
        self.folder_selection_status.setPixmap(QPixmap("files/cross_icon.png"))

        spacer_status_browse = QSpacerItem(60, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.browse_video_button = QPushButton(self.file_selection_widget)
        self.browse_video_button.setFont(self.font_bold_10)
        self.browse_video_button.setObjectName("secondary_button")
        self.browse_video_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.browse_xml_button = QPushButton(self.file_selection_widget)
        self.browse_xml_button.setFont(self.font_bold_10)
        self.browse_xml_button.setObjectName("secondary_button")
        self.browse_xml_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.browse_folder_button = QPushButton(self.file_selection_widget)
        self.browse_folder_button.setFont(self.font_bold_10)
        self.browse_folder_button.setObjectName("secondary_button")
        self.browse_folder_button.setCursor(QCursor(Qt.PointingHandCursor))

        spacer_browse_path = QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.videopath_label = DropLabel(self.file_selection_widget)
        self.videopath_label.define_type("video")
        self.videopath_label.setFont(self.default_font)
        self.videopath_label.setAlignment(Qt.AlignCenter)
        self.videopath_label.setObjectName("default_label")
        self.xmlpath_label = DropLabel(self.file_selection_widget)
        self.xmlpath_label.define_type("xml")
        self.xmlpath_label.setFont(self.default_font)
        self.xmlpath_label.setAlignment(Qt.AlignCenter)
        self.xmlpath_label.setObjectName("default_label")
        self.folderpath_label = DropLabel(self.file_selection_widget)
        self.folderpath_label.define_type("folder")
        self.folderpath_label.setFont(self.default_font)
        self.folderpath_label.setAlignment(Qt.AlignCenter)
        self.folderpath_label.setObjectName("default_label")

        self.delete_video_selection_button = QPushButton(self.file_selection_widget)
        self.delete_video_selection_button.setObjectName("delete_button")
        self.delete_video_selection_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_xml_selection_button = QPushButton(self.file_selection_widget)
        self.delete_xml_selection_button.setObjectName("delete_button")
        self.delete_xml_selection_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_folder_selection_button = QPushButton(self.file_selection_widget)
        self.delete_folder_selection_button.setObjectName("delete_button")
        self.delete_folder_selection_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.use_xml_radio = QRadioButton(self.file_selection_widget)
        self.use_xml_radio.setText("Use XML video starting time")
        self.use_xml_radio.setChecked(True)
        self.use_xml = True

        self.use_no_xml_radio = QRadioButton(self.file_selection_widget)
        self.use_no_xml_radio.setText("Use custom video starting time")
        self.use_no_xml_radio.setChecked(False)
        self.use_no_xml_radio.toggled.connect(self.toggle_xml_usage)

        self.select_starting_time_button = QPushButton(self)
        self.select_starting_time_button.setText("SELECT")
        self.select_starting_time_button.setFixedSize(100, 33)
        self.select_starting_time_button.setObjectName("secondary_button")
        self.select_starting_time_button.setFont(self.font_bold_10)
        self.select_starting_time_button.setVisible(False)
        self.select_starting_time_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.file_selection_grid.addWidget(self.video_selection_status, 0, 0, 1, 1)
        self.file_selection_grid.addWidget(self.xml_selection_status, 4, 0, 1, 1)
        self.file_selection_grid.addWidget(self.folder_selection_status, 1, 0, 1, 1)
        self.file_selection_grid.addItem(spacer_status_browse, 0, 1, 3, 1)
        self.file_selection_grid.addWidget(self.browse_video_button, 0, 2, 1, 1)
        self.file_selection_grid.addWidget(self.browse_xml_button, 4, 2, 1, 1)
        self.file_selection_grid.addWidget(self.browse_folder_button, 1, 2, 1, 1)
        self.file_selection_grid.addItem(spacer_browse_path, 0, 3, 3, 1)
        self.file_selection_grid.addWidget(self.videopath_label, 0, 4, 1, 1)
        self.file_selection_grid.addWidget(self.xmlpath_label, 4, 4, 1, 1)
        self.file_selection_grid.addWidget(self.folderpath_label, 1, 4, 1, 1)
        self.file_selection_grid.addWidget(self.delete_video_selection_button, 0, 5, 1, 1)
        self.file_selection_grid.addWidget(self.delete_xml_selection_button, 4, 5, 1, 1)
        self.file_selection_grid.addWidget(self.delete_folder_selection_button, 1, 5, 1, 1)
        self.file_selection_grid.addWidget(self.use_xml_radio, 2, 2, 1, 1)
        self.file_selection_grid.addWidget(self.use_no_xml_radio, 3, 2, 1, 1)
        self.file_selection_grid.addWidget(self.select_starting_time_button, 3, 3, 1, 2)

        # Defaults section
        self.defaults_group = QGroupBox(self.centralwidget)
        self.defaults_group.setGeometry(430, 20, 480, 80)
        self.defaults_group.setFont(self.font_normal_10)
        self.defaults_group.setFlat(True)

        self.apply_defaults_button = QPushButton(self.defaults_group)
        self.apply_defaults_button.setGeometry(20, 30, 130, 33)
        self.apply_defaults_button.setFont(self.font_bold_9)
        self.apply_defaults_button.setObjectName("tertiary_button")
        self.apply_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.set_defaults_button = QPushButton(self.defaults_group)
        self.set_defaults_button.setGeometry(160, 30, 120, 33)
        self.set_defaults_button.setFont(self.font_bold_9)
        self.set_defaults_button.setObjectName("tertiary_button")
        self.set_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_defaults_button = QPushButton(self.defaults_group)
        self.delete_defaults_button.setGeometry(290, 30, 140, 33)
        self.delete_defaults_button.setFont(self.font_bold_9)
        self.delete_defaults_button.setObjectName("tertiary_button")
        self.delete_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.help_defaults_button = QPushButton(self.centralwidget)
        self.help_defaults_button.setGeometry(870, 25, 32, 32)
        self.help_defaults_button.setText("?")
        self.help_defaults_button.setFont(self.font_bold_14)
        self.help_defaults_button.setObjectName("help_defaults_button")
        self.help_defaults_button.setCursor(QCursor(Qt.PointingHandCursor))

        # Analyse section
        self.analyse_widget = QWidget(self.centralwidget)
        self.analyse_widget.setGeometry(20, 450, 250, 71)
        self.analyse_layout = QHBoxLayout(self.analyse_widget)
        self.analyse_layout.setContentsMargins(0, 0, 0, 0)

        self.analysation_status_image = QLabel(self.analyse_widget)
        self.analysation_status_image.setPixmap(QPixmap("files/cross_icon.png"))

        spacer_status_analyse = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)

        self.analyse_button = QPushButton(self.analyse_widget)
        self.analyse_button.setFont(self.font_bold_15)
        self.analyse_button.setObjectName("primary_button")
        self.analyse_button.setFixedWidth(170)
        self.analyse_button.setFixedHeight(50)
        self.analyse_button.setCursor(QCursor(Qt.PointingHandCursor))

        self.analyse_layout.addWidget(self.analysation_status_image)
        self.analyse_layout.addItem(spacer_status_analyse)
        self.analyse_layout.addWidget(self.analyse_button)

        # Setup the central widget
        self.setCentralWidget(self.centralwidget)

        # Add a menubar
        self.menubar = QMenuBar(self)
        self.filemenu = QMenu(self.menubar)
        # self.languagemenu = QMenu(self.menubar)
        # self.languagemenu.setDisabled(True)
        self.setMenuBar(self.menubar)

        self.actionOpen = QAction(self)
        self.actionSave = QAction(self)
        self.actionSettings = QAction(self)
        self.actionQuit = QAction(self)

        # self.actionGerman = QAction(self)
        # self.actionEnglish = QAction(self)

        self.filemenu.addAction(self.actionOpen)
        self.filemenu.addAction(self.actionSave)
        self.filemenu.addAction(self.actionSettings)
        self.filemenu.addSeparator()
        self.filemenu.addAction(self.actionQuit)
        # self.languagemenu.addAction(self.actionGerman)
        # self.languagemenu.addAction(self.actionEnglish)
        self.menubar.addAction(self.filemenu.menuAction())
        # self.menubar.addAction(self.languagemenu.menuAction())

        # Add a statusbar
        self.statusbar = QStatusBar(self)
        self.setStatusBar(self.statusbar)

        # Add all the text
        self.browse_video_button.setText("BROWSE")
        self.browse_xml_button.setText("BROWSE")
        self.browse_folder_button.setText("BROWSE")
        self.videopath_label.setText('Please press "Browse" or drag & drop a video to select it')
        self.xmlpath_label.setText('Please press "Browse" or drag & drop an XML file to select it')
        self.folderpath_label.setText('Please press "Browse" or drag & drop a folder to select it')

        self.defaults_group.setTitle("Defaults")
        self.set_defaults_button.setText("Set defaults")
        self.apply_defaults_button.setText("Apply defaults")
        self.delete_defaults_button.setText("Delete defaults")

        self.analyse_button.setText("ANALYSE")

        self.browse_video_button.setToolTip("Browse to select a video to process.")
        self.browse_xml_button.setToolTip("Browse to select an xml file.")
        self.browse_folder_button.setToolTip("Browse to select a folder to store results in.")
        self.video_selection_status.setToolTip("Status:\nNot yet completed!")
        self.xml_selection_status.setToolTip("Status:\nNot yet completed!")
        self.folder_selection_status.setToolTip("Status:\nNot yet completed!")
        self.analysation_status_image.setToolTip("Status:\nNot yet completed!")
        self.delete_video_selection_button.setToolTip("Clear your video selection.")
        self.delete_xml_selection_button.setToolTip("Clear your xml selection.")
        self.delete_folder_selection_button.setToolTip("Clear your folder selection.")
        self.help_defaults_button.setToolTip("What are defaults?")
        self.analyse_button.setToolTip("Analyse the selected video.")

        self.filemenu.setTitle("File")
        self.actionOpen.setText("Open")
        self.actionOpen.setShortcut("Ctrl+O")
        self.actionSave.setText("Save")
        self.actionSave.setShortcut("Ctrl+S")
        self.actionSettings.setText("Settings")
        self.actionSettings.setShortcut("Ctrl+Shift+P")
        self.actionQuit.setText("Quit")
        self.actionQuit.setShortcut("Ctrl+Q")

        self.browse_video_button.clicked.connect(self.get_video_location)
        self.browse_xml_button.clicked.connect(self.get_xml_location)
        self.browse_folder_button.clicked.connect(self.get_folder_location)
        self.select_starting_time_button.clicked.connect(self.select_starting_time)
        self.delete_video_selection_button.clicked.connect(self.delete_video_selection)
        self.delete_xml_selection_button.clicked.connect(self.delete_xml_selection)
        self.delete_folder_selection_button.clicked.connect(self.delete_folder_selection)
        self.apply_defaults_button.clicked.connect(self.apply_defaults)
        self.set_defaults_button.clicked.connect(self.set_defaults)
        self.delete_defaults_button.clicked.connect(self.delete_defaults)
        self.help_defaults_button.clicked.connect(self.help_defaults)
        self.analyse_button.clicked.connect(self.analyse)

        self.actionQuit.triggered.connect(sys.exit)
        self.actionOpen.triggered.connect(self.open_vamos_file)
        self.actionSave.triggered.connect(self.save_vamos_file)
        self.actionSettings.triggered.connect(self.open_settings)

    def setup_video_selection(self, videopath_list):
        self.videopath_list = videopath_list
        if self.videopath_list:  # If the user didn't cancel the selection
            thumbnail = get_thumbnail(self.videopath_list[0])
            if thumbnail.any() is None:
                return
            height, width, _ = thumbnail.shape
            bytes_per_line = 3 * width
            video_thumbnail = QImage(thumbnail.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.video_thumb.setPixmap(QPixmap(video_thumbnail))
            self.VideoID_List = []
            self.videopath_string = ""
            for video in self.videopath_list:
                self.VideoID_List.append(video[-10:-4])
            if len(self.videopath_list) == 1:
                self.videopath_string = self.videopath_list[0]
                if len(self.videopath_string) > 50:
                    self.videopath_string = f"{self.videopath_string[:3]} [ . . . ] {self.videopath_string[-50:]}"
                self.videopath_label.setText("Video:\n" + self.videopath_string)
            else:
                for i in range(1):
                    video = self.videopath_list[i]
                    if len(video) > 50:
                        video = f"{video[:3]} [ . . . ] {video[-50:]}"
                    self.videopath_string += f"\n{video}"
                self.videopath_string += f"\n... and {str(len(self.videopath_list) - 1)} more"
                self.videopath_label.setText("Videos:" + self.videopath_string)
            self.video_selection_status.setPixmap(QPixmap("files/check_icon.png"))
            self.video_selection_status.setToolTip("Status:\nCompleted!")

    def setup_xml_selection(self, xmlpath_list):
        self.xmlpath_list = xmlpath_list
        if self.xmlpath_list:  # If the user didn't cancel the selection
            self.xmlpath_string = ""
            if len(self.xmlpath_list) == 1:
                self.xmlpath_string = self.xmlpath_list[0]
                if len(self.xmlpath_string) > 50:
                    self.xmlpath_string = f"{self.xmlpath_string[:3]} [ . . . ] {self.xmlpath_string[-50:]}"
                self.xmlpath_label.setText("XML:\n" + self.xmlpath_string)
            else:
                for i in range(1):
                    xml = self.xmlpath_list[i]
                    if len(xml) > 50:
                        xml = f"{xml[:3]} [ . . . ] {xml[-50:]}"
                    self.xmlpath_string += f"\n{xml}"
                self.xmlpath_string += f"\n... and {str(len(self.xmlpath_list) - 1)} more"
                self.xmlpath_label.setText("XMLs:" + self.xmlpath_string)
            self.xml_selection_status.setPixmap(QPixmap("files/check_icon.png"))
            self.xml_selection_status.setToolTip("Status:\nCompleted!")

    def setup_folder_selection(self, folderpath):
        self.folderpath = folderpath
        if self.folderpath != "":  # If the user didn't cancel the selection
            if len(self.folderpath) > 50:
                self.folderpath_string = f"{self.folderpath[:3]} [ . . . ] {self.folderpath[-50:]}"
            else:
                self.folderpath_string = self.folderpath
            self.folderpath_label.setText("Results folder:\n" + self.folderpath_string)

            self.folder_selection_status.setPixmap(QPixmap("files/check_icon.png"))
            self.folder_selection_status.setToolTip("Status:\nCompleted!")

    def get_video_location(self):
        self.videopath_list = QFileDialog.getOpenFileNames(parent=self, filter="MP4 Files (*.mp4)")
        self.videopath_list = self.videopath_list[0]
        self.setup_video_selection(self.videopath_list)

    def get_xml_location(self):
        self.xmlpath_list = QFileDialog.getOpenFileNames(parent=self, filter="XML Files (*.xml)")
        self.xmlpath_list = self.xmlpath_list[0]
        self.setup_xml_selection(self.xmlpath_list)

    def get_folder_location(self):
        self.folderpath = QFileDialog.getExistingDirectory(parent=self)
        self.setup_folder_selection(self.folderpath)

    def delete_video_selection(self):
        try:
            self.videopath_label.setText('Please press "Browse" or drag & drop a video to select it')
            self.video_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
            del self.videopath_list
            self.video_thumb.setPixmap(QPixmap("files/default_thumbnail.png"))
            self.video_selection_status.setToolTip("Status:\nNot yet completed!")
        except AttributeError:
            pass

    def delete_xml_selection(self):
        try:
            self.xmlpath_label.setText('Please press "Browse" or drag & drop an XML file to select it')
            self.xml_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
            del self.xmlpath_list
            self.xml_selection_status.setToolTip("Status:\nNot yet completed!")
        except AttributeError:
            pass

    def delete_folder_selection(self):
        try:
            self.folderpath_label.setText('Please press "Browse" or drag & drop a folder to select it')
            self.folder_selection_status.setPixmap(QPixmap("files/cross_icon.png"))
            del self.folderpath
            self.folder_selection_status.setToolTip("Status:\nNot yet completed!")
        except AttributeError:
            pass

    @staticmethod
    def help_defaults():
        help_defaults_message = QMessageBox()
        help_defaults_message.setWindowTitle("What are defaults?")
        help_defaults_message.setText(
            "Defaults are not required for the program to work. They let you quickly fill out the video, "
            "xml and folderpath with predefined values. You should only use them if you analyse the same video over "
            "and over again.")
        help_defaults_message.setIcon(QMessageBox.Question)
        help_defaults_message.setStandardButtons(QMessageBox.Ok)

        help_defaults_message.exec_()

    def analyse(self):
        try:
            self.meteor_data = {}
            self.meteor_count = 0

            self.length_list = []
            self.fps_list = []
            # TODO: Use a resolution list instead: [[height, width], ...] and update all other instances
            self.height_list = []
            self.width_list = []
            self.base_time_list = []

            for self.video_index in range(len(self.videopath_list)):
                meta_data_video = cv2.VideoCapture(self.videopath_list[self.video_index])
                self.length = int(meta_data_video.get(cv2.CAP_PROP_FRAME_COUNT))
                self.Fps = int(meta_data_video.get(cv2.CAP_PROP_FPS))
                self.Height = int(meta_data_video.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.Width = int(meta_data_video.get(cv2.CAP_PROP_FRAME_WIDTH))

                if self.broke_frame != 0:
                    continue_at_breaking_point = QMessageBox.question(Window, "Continue?",
                                                                      "Do you want to continue where you left?",
                                                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                    if continue_at_breaking_point == QMessageBox.Yes:
                        self.start_frame = self.broke_frame - 1
                    else:
                        self.start_frame = 0
                else:
                    self.start_frame = 0

                if self.use_xml:
                    self.was_successful, self.video_meteor_data, self.sort_out_list, self.base_time_separated = analyse_diff(
                        self.videopath_list[self.video_index],
                        self.xmlpath_list[self.video_index],
                        self.folderpath,
                        self.VideoID_List[self.video_index],
                        Window,
                        True)
                else:
                    self.was_successful, self.video_meteor_data, self.sort_out_list, self.base_time_separated = analyse_diff(
                        self.videopath_list[self.video_index],
                        None,
                        self.folderpath,
                        self.VideoID_List[self.video_index],
                        Window,
                        False)

                self.length_list.append(self.length)
                self.fps_list.append(self.Fps)
                self.height_list.append(self.Height)
                self.width_list.append(self.Width)
                self.base_time_list.append(self.base_time_separated)

                video_id = self.VideoID_List[self.video_index]

                self.meteor_data[video_id] = self.video_meteor_data

                self.meteor_data[video_id][video_id] = self.base_time_separated

            if self.was_successful:
                self.unsaved_changes = True
                self.setWindowTitle("VAMOS+ - Video-Assisted Meteor Observation System [unsaved changes]")

                self.analysation_status_image.setPixmap(QPixmap("files/check_icon.png"))
                self.analysation_status_image.setToolTip("Status:\nCompleted!")

        except ArithmeticError as a:
            self.analyse_error_message = QMessageBox(icon=QMessageBox.Critical,
                                                     text='The analysation algorithm needs three paths:\n    1. The '
                                                          'video to process.\n    2. The beginning of the video, either'
                                                          ' from an XML-File or \n        the manual picker'
                                                          '\n    3. The folder where it saves images '
                                                          'of frames with meteors.')
            self.analyse_error_message.setWindowTitle("File selection missing!")
            self.analyse_error_message.setInformativeText(
                '<h3><strong>To select these infos, press the blue "Browse" buttons.</strong></h3>')
            self.analyse_error_message.setDetailedText("Error message:\n" + str(a))
            self.analyse_error_message.setStandardButtons(QMessageBox.Close)
            self.analyse_error_message.exec_()

    @staticmethod
    def apply_defaults():
        apply_defaults(Window)

    @staticmethod
    def set_defaults():
        set_defaults(Window)

    @staticmethod
    def delete_defaults():
        delete_defaults(Window)

    def toggle_xml_usage(self):
        if self.use_no_xml_radio.isChecked():
            self.use_xml = False
            self.delete_xml_selection()
            self.xml_selection_status.setVisible(False)
            self.browse_xml_button.setVisible(False)
            self.xmlpath_label.setVisible(False)
            self.delete_xml_selection_button.setVisible(False)
            self.select_starting_time_button.setVisible(True)
        else:
            self.use_xml = True
            self.xml_selection_status.setVisible(True)
            self.browse_xml_button.setVisible(True)
            self.xmlpath_label.setVisible(True)
            self.delete_xml_selection_button.setVisible(True)
            self.select_starting_time_button.setVisible(False)

    def select_starting_time(self):
        try:
            _ = self.videopath_list
            _ = self.folderpath
            date_picker_popup = DatePickerPopup()
            date_picker_popup.exec_()
        except AttributeError:
            self.video_not_defined = QMessageBox()
            self.video_not_defined.setWindowTitle("No video selected!")
            self.video_not_defined.setText('To be able to select the video starting time, you have to select a video.')
            self.video_not_defined.setInformativeText(
                '<h3><strong>For that, press the first blue "Browse" button.</strong></h3>')
            self.video_not_defined.setIcon(QMessageBox.Critical)
            self.video_not_defined.setStandardButtons(QMessageBox.Close)
            self.video_not_defined.exec_()

    def open_vamos_file(self):
        if self.vamos_file_path == "":
            vamos_filepath = QFileDialog.getOpenFileName(
                self, caption="Select VAMOS File", filter="VAMOS Files (*.vamos)")[0]
        else:
            vamos_filepath = self.vamos_file_path
        if vamos_filepath != "":
            self.vamos_file_path = ""
            self.results_window = ResultsWindow(vamos_filepath)
            self.results_window.show()

    def save_vamos_file(self):
        if not self.was_successful:
            run_analysation_first = QMessageBox(icon=QMessageBox.Critical, text="To save an VAMOS-File, run the "
                                                                                "analysation first.")
            run_analysation_first.setWindowTitle("No results")
            run_analysation_first.exec_()
            return False
        vamos_filepath = QFileDialog.getSaveFileName(self,
                                                     "Select a directory to save the VAMOS file in",
                                                     self.folderpath + "/" + self.VideoID_List[0] + ".vamos",
                                                     "VAMOS Files (*.vamos)")[0]
        if vamos_filepath != "":
            write_vamos_file(self.Fps, vamos_filepath, self.meteor_data, self.sort_out_list,
                             self.base_time_list, self.videopath_list, self.xmlpath_list, self.folderpath,
                             self.length_list, self.fps_list, [self.width_list, self.height_list])
        else:
            return False
        self.unsaved_changes = False
        self.setWindowTitle("VAMOS+ - Video-Assisted Meteor Observation System")
        return True

    def open_settings(self):
        self.settings_window = SettingsWindow()
        self.settings_window.show()

    def closeEvent(self, event):
        if self.unsaved_changes and self.was_successful:
            save_changes = QMessageBox.question(Window, "Analysation results modified", "Save changes before closing?",
                                                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                                QMessageBox.Save)
            if save_changes == QMessageBox.Discard:
                event.accept()
            elif save_changes == QMessageBox.Cancel:
                event.ignore()
            else:
                a = self.save_vamos_file()
                if a:
                    event.accept()
                else:
                    event.ignore()
        else:
            event.accept()


def vamos_error_handler(exctype, value, tb):
    error_message_box = QMessageBox(icon=QMessageBox.Critical,
                                    text=f'The following unknown error occurred:\n{exctype.__name__}: {value}')
    error_message_box.setInformativeText(
        '<strong>Please contact the developer of this program to fix the problem!</strong>')
    error_message_box.setWindowTitle("Unknown error occurred")
    error_message_box.exec_()


# sys.excepthook = vamos_error_handler

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
app = QApplication(sys.argv)
app.setStyleSheet(StyleSheet)

Window = AnalysationWindow()
Window.show()

if Window.vamos_file_path != "":
    Window.open_vamos_file()

sys.exit(app.exec_())
