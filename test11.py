import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QDialog, QCheckBox, QDialogButtonBox,
    QStackedLayout, QFrame, QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class DataPointsDialog(QDialog):
    def __init__(self, selected_points=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select and Name Data Points")
        self.selected_points = selected_points or []
        self.checkboxes = []
        self.line_edits = []

        layout = QVBoxLayout()
        for i in range(1, 17):
            point_name = f"Data Point {i}"
            default_checked = False
            custom_name = point_name

            for entry in self.selected_points:
                if entry.get("index") == i:
                    default_checked = entry.get("checked", False)
                    custom_name = entry.get("name", point_name)
                    break

            checkbox = QCheckBox()
            checkbox.setChecked(default_checked)

            line_edit = QLineEdit()
            line_edit.setText(custom_name)

            self.checkboxes.append(checkbox)
            self.line_edits.append(line_edit)

            row_layout = QHBoxLayout()
            row_layout.addWidget(checkbox)
            row_layout.addWidget(line_edit)
            layout.addLayout(row_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_selected_points(self):
        result = []
        for i, (cb, le) in enumerate(zip(self.checkboxes, self.line_edits), 1):
            result.append({
                "index": i,
                "checked": cb.isChecked(),
                "name": le.text()
            })
        return result

class ConfigureCameraDialog(QDialog):
    def __init__(self, current_rtsp='', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Camera")
        self.rtsp_link = current_rtsp

        layout = QVBoxLayout()
        self.rtsp_input = QLineEdit()
        self.rtsp_input.setText(current_rtsp)
        self.rtsp_input.setPlaceholderText("Enter RTSP link")
        layout.addWidget(self.rtsp_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_rtsp_link(self):
        return self.rtsp_input.text()

class CameraWidget(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.main_window = parent
        self.rtsp_link = ""
        self.selected_data_points = []

        layout = QVBoxLayout()

        self.video_label = QLabel(f"{name} View")
        self.video_label.setStyleSheet("background-color: black; color: white;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.video_label.setMinimumSize(320, 240)
        self.video_label.mouseDoubleClickEvent = self.toggle_fullscreen
        layout.addWidget(self.video_label)

        # STATUS INDICATORS AS COMPACT LABELS
        status_labels = [
            "CAMERA HEALTH", "AIR PRESS", "AIR TEMP",
            "AIR FILT CLOG", "CAM TEMP", "CAMERA REM"
        ]
        status_layout = QHBoxLayout()
        status_layout.setSpacing(6)
        for text in status_labels:
            label = QLabel(text)
            label.setStyleSheet("""
                QLabel {
                    background-color: #e0e0e0;
                    font-weight: bold;
                    font-size: 10pt;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 3px 8px;
                }
            """)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(28)
            status_layout.addWidget(label)
        layout.addLayout(status_layout)

        # CONTROL BUTTONS
        self.configure_btn = QPushButton("CONFIGURE")
        self.take_in_btn = QPushButton("CAMERA INSERT")
        self.take_out_btn = QPushButton("CAMERA RETRACT")
        self.view_data_btn = QPushButton("VIEW DATA POINTS")

        for btn in [self.configure_btn, self.take_in_btn, self.take_out_btn, self.view_data_btn]:
            btn.setStyleSheet("QPushButton { background-color: lightgrey; font-weight: bold; border: 1px solid #ccc; border-radius: 5px; padding: 6px 12px; } QPushButton:hover { background-color: #d3d3d3; border-color: #999; }")

        self.configure_btn.clicked.connect(self.configure_camera)
        self.view_data_btn.clicked.connect(self.open_data_dialog)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.addWidget(self.configure_btn)
        ctrl_layout.addWidget(self.take_in_btn)
        ctrl_layout.addWidget(self.take_out_btn)
        ctrl_layout.addWidget(self.view_data_btn)
        layout.addLayout(ctrl_layout)

        self.setLayout(layout)

    def open_data_dialog(self):
        dialog = DataPointsDialog(selected_points=self.selected_data_points, parent=self)
        if dialog.exec_():
            self.selected_data_points = dialog.get_selected_points()
            selected_names = [dp["name"] for dp in self.selected_data_points if dp["checked"]]
            QMessageBox.information(self, "Data Points Saved", f"Saved data points for {self.name}:\n" + ", ".join(selected_names))
            if self.main_window.stack_layout.currentWidget() == self.main_window.fullscreen_frame:
                self.main_window.show_data_sidebar(self)

    def toggle_fullscreen(self, event):
        self.main_window.toggle_camera_fullscreen(self)

    def configure_camera(self):
        dialog = ConfigureCameraDialog(current_rtsp=self.rtsp_link, parent=self)
        if dialog.exec_():
            self.rtsp_link = dialog.get_rtsp_link()
            QMessageBox.information(self, "RTSP Saved", f"{self.name} RTSP link saved:\n{self.rtsp_link}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TOSHNIWAL INDUSTRIES PVT. LTD.")
        self.setWindowState(Qt.WindowMaximized)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.stack_layout = QStackedLayout()
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.grid_widget.setLayout(self.grid_layout)

        self.camera_widgets = []
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        for i, pos in enumerate(positions):
            cam = CameraWidget(f"Camera {i+1}", parent=self)
            self.grid_layout.addWidget(cam, *pos)
            self.camera_widgets.append(cam)

        self.stack_layout.addWidget(self.grid_widget)

        self.fullscreen_frame = QFrame()
        self.fullscreen_layout = QVBoxLayout()
        self.fullscreen_frame.setLayout(self.fullscreen_layout)

        self.fullscreen_split = QHBoxLayout()
        self.fullscreen_layout.addLayout(self.fullscreen_split)

        self.fullscreen_camera_container = QWidget()
        self.fullscreen_camera_layout = QVBoxLayout()
        self.fullscreen_camera_container.setLayout(self.fullscreen_camera_layout)

        self.sidebar_widget = QWidget()
        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setAlignment(Qt.AlignTop)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_widget.setLayout(self.sidebar_layout)
        self.sidebar_widget.setFixedWidth(250)
        self.sidebar_widget.hide()

        self.fullscreen_split.addWidget(self.fullscreen_camera_container)
        self.fullscreen_split.addWidget(self.sidebar_widget)

        self.stack_layout.addWidget(self.fullscreen_frame)

        main_layout = QVBoxLayout()
        main_layout.addLayout(self.stack_layout)
        self.central_widget.setLayout(main_layout)

    def toggle_camera_fullscreen(self, camera_widget):
        if self.stack_layout.currentWidget() == self.grid_widget:
            self.grid_widget.hide()
            for i in reversed(range(self.fullscreen_camera_layout.count())):
                self.fullscreen_camera_layout.itemAt(i).widget().setParent(None)
            self.fullscreen_camera_layout.addWidget(camera_widget)
            self.stack_layout.setCurrentWidget(self.fullscreen_frame)
        else:
            self.fullscreen_camera_layout.removeWidget(camera_widget)
            self.stack_layout.setCurrentWidget(self.grid_widget)
            for idx, cam in enumerate(self.camera_widgets):
                row, col = divmod(idx, 2)
                self.grid_layout.addWidget(cam, row, col)
            self.sidebar_widget.hide()

    def show_data_sidebar(self, camera_widget):
        for i in reversed(range(self.sidebar_layout.count())):
            self.sidebar_layout.itemAt(i).widget().deleteLater()

        selected = [dp["name"] for dp in camera_widget.selected_data_points if dp["checked"]]
        if not selected:
            self.sidebar_widget.hide()
            return

        title = QLabel(f"<b>{camera_widget.name} - Data Points:</b>")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("padding: 6px; font-size: 14px;")
        self.sidebar_layout.addWidget(title)

        for name in selected:
            label = QLabel(f"{name}:")
            label.setFixedSize(230, 30)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: #dceeff;
                    padding-left: 10px;
                    font-family: Courier New, Courier, monospace;
                    font-size: 13px;
                    border: 1px solid #aaa;
                    margin-bottom: 4px;
                }
            """)
            self.sidebar_layout.addWidget(label)

        self.sidebar_widget.setStyleSheet("background-color: #f2f2f2; border-left: 2px solid #aaa;")
        self.sidebar_widget.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
