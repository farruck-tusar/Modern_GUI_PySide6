import logging
import os
import sys

from PySide6.QtCore import Slot, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QWidget, QVBoxLayout

from application import Settings
from widgets.video_player.ui_video_player import Ui_videoPlayer
from yolov5 import detect


def run_yolov5_detection(video_path):
    venv_directory = Settings.VENV_DIR

    activate_script = 'bin/activate' if sys.platform != 'win32' else 'Scripts\\activate'
    venv_activate_script = os.path.join(venv_directory, activate_script)

    python_path = 'bin/python' if sys.platform != 'win32' else 'Scripts\\python'
    venv_python_path = os.path.join(venv_directory, python_path)

    # logging.info("[START] venv activation")
    # activate_cmd = f'source {venv_activate_script}' if sys.platform != 'win32' else venv_activate_script
    # subprocess.run(activate_cmd, shell=True)
    # logging.info("[END] venv activation")

    logging.info("[START] YOLOv5 detection")
    detect.run(source=video_path,
               weights=os.path.join(Settings.YOLO_WEIGHT_DIR),
               project=os.path.join(Settings.OUTPUT_DIR, Settings.OUTPUT_FOLDER_NAME),
               conf_thres=0.5,
               save_txt=True)
    logging.info("[END] YOLOv5 detection")

    # logging.info("[START] venv deactivation")
    # if sys.platform == 'win32':
    #     subprocess.run('deactivate', shell=True)
    # else:
    #     subprocess.run('deactivate', shell=True)
    # logging.info("[END] venv deactivation")


class VideoPlayer(Ui_videoPlayer, QWidget):
    def __init__(self, main_ui, video_path):
        super().__init__(main_ui)
        self.ui = Ui_videoPlayer()
        self.ui.setupUi(self)

        self.ui.btn_back.clicked.connect(lambda: main_ui.stackedWidget.setCurrentWidget(main_ui.page_loadVideos))
        self.ui.btn_process.clicked.connect(lambda: run_yolov5_detection(video_path))

        self._video_widget = QVideoWidget()
        QVBoxLayout(self.ui.frame_player).addWidget(self._video_widget)

        self._player = QMediaPlayer()
        self._player.errorOccurred.connect(self._player_error)

        self._player.setVideoOutput(self._video_widget)
        self._player.setSource(video_path)

        # Initialize icons
        self._play_icon = QIcon(":icons/icons/cil-media-play.png")
        self._pause_icon = QIcon(":icons/icons/cil-media-pause.png")
        self._play_action = self.ui.btn_play
        self._play_action.setIcon(self._play_icon)
        self._play_action.clicked.connect(self.toggle_play_pause)

        self._stop_action = self.ui.btn_stop
        self._stop_action.clicked.connect(self._player.stop)

        self._player.playbackStateChanged.connect(self.update_buttons)

        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self.update_video_position)
        self._update_timer.start(100)

    @Slot("QMediaPlayer::PlaybackState")
    def update_buttons(self, state):
        self._stop_action.setEnabled(state != QMediaPlayer.StoppedState)

        if state == QMediaPlayer.PlayingState:
            self._play_action.setText("Pause")
            self._play_action.setIcon(self._pause_icon)
        else:
            self._play_action.setText("Play")
            self._play_action.setIcon(self._play_icon)

    @Slot("QMediaPlayer::Error", str)
    def _player_error(self, error, error_string):
        print(error_string, file=sys.stderr)

    def toggle_play_pause(self):
        if self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def closeEvent(self, event):
        self._ensure_stopped()
        event.accept()

    @Slot()
    def _ensure_stopped(self):
        if self._player.playbackState() != QMediaPlayer.StoppedState:
            self._player.stop()

    def update_video_position(self):
        if self._player.duration() > 0:
            position = self._player.position()
            duration = self._player.duration()
            formatted_position = self.format_time(position)
            formatted_duration = self.format_time(duration)
            self.ui.label_time.setText(f"{formatted_position}/{formatted_duration}")
            self.ui.slider_time.setMaximum(duration)
            self.ui.slider_time.setValue(position)

    @staticmethod
    def format_time(milliseconds):
        total_seconds = milliseconds // 1000
        milliseconds_remainder = milliseconds % 1000
        seconds = total_seconds % 60
        minutes = (total_seconds // 60) % 60
        hours = total_seconds // 3600
        return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds_remainder:03}"
