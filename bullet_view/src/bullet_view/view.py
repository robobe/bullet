"""FlightLens-themed PySide6 view for Bullet telemetry."""
from math import degrees

from PySide6 import QtCore, QtGui, QtWidgets

from .model import TelemetrySnapshot


WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 720
MAX_ALTITUDE_M = 30.
PITCH_PIXELS_PER_RAD = 85.


class FlightBall(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.attitude = None
        self.setMinimumSize(360, 360)
        self.setAccessibleName('Flight attitude ball')

    def set_attitude(self, attitude):
        self.attitude = attitude
        self.update()

    def paintEvent(self, event):
        del event
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height()) - 28
        radius = size / 2
        center = QtCore.QPointF(self.width() / 2, self.height() / 2)
        painter.setPen(QtGui.QPen(QtGui.QColor('#70d6ad'), 3))
        painter.setBrush(QtGui.QColor('#101c2a'))
        painter.drawEllipse(center, radius, radius)
        painter.save()
        clip = QtGui.QPainterPath()
        clip.addEllipse(center, radius - 2, radius - 2)
        painter.setClipPath(clip)
        roll = 0. if self.attitude is None else degrees(self.attitude.roll_rad)
        pitch = 0. if self.attitude is None else self.attitude.pitch_rad * PITCH_PIXELS_PER_RAD
        painter.translate(center)
        painter.rotate(-roll)
        painter.translate(0, pitch)
        painter.fillRect(QtCore.QRectF(-radius * 2, -radius * 2, radius * 4, radius * 2), QtGui.QColor('#284c68'))
        painter.fillRect(QtCore.QRectF(-radius * 2, 0, radius * 4, radius * 2), QtGui.QColor('#9b694e'))
        painter.setPen(QtGui.QPen(QtGui.QColor('#d9e6f4'), 2))
        painter.drawLine(QtCore.QPointF(-radius * 2, 0), QtCore.QPointF(radius * 2, 0))
        painter.restore()
        painter.setPen(QtGui.QPen(QtGui.QColor('#eab85a'), 3))
        painter.drawLine(center + QtCore.QPointF(-radius * .42, 0), center + QtCore.QPointF(-radius * .12, 0))
        painter.drawLine(center + QtCore.QPointF(radius * .12, 0), center + QtCore.QPointF(radius * .42, 0))
        painter.end()


class AltitudeWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.altitude_m = None
        self.setMinimumSize(220, 360)
        self.setAccessibleName('Altitude gauge')

    def set_altitude(self, altitude):
        self.altitude_m = None if altitude is None else altitude.local_m
        self.update()

    def paintEvent(self, event):
        del event
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor('#30485f'), 1))
        painter.setBrush(QtGui.QColor('#101c2a'))
        painter.drawRoundedRect(self.rect().adjusted(8, 8, -8, -8), 8, 8)
        painter.setPen(QtGui.QColor('#d9e6f4'))
        painter.setFont(QtGui.QFont('sans-serif', 15, QtGui.QFont.Weight.Bold))
        text = 'Unavailable' if self.altitude_m is None else f'{self.altitude_m:.2f} m'
        painter.drawText(self.rect().adjusted(20, 24, -20, -20), QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter, text)
        top, bottom = 86, self.height() - 28
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor('#203950'))
        painter.drawRoundedRect(self.width() / 2 - 18, top, 36, bottom - top, 8, 8)
        if self.altitude_m is not None:
            fraction = max(0., min(1., self.altitude_m / MAX_ALTITUDE_M))
            painter.setBrush(QtGui.QColor('#58b8f5'))
            height = (bottom - top) * fraction
            painter.drawRoundedRect(self.width() / 2 - 18, bottom - height, 36, height, 8, 8)
        painter.end()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, presenter):
        super().__init__()
        self.presenter = presenter
        self.setWindowTitle('Bullet View · MAVLink Telemetry')
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(820, 560)
        self.setStyleSheet('''
            QMainWindow, QWidget { background:#142233; color:#d9e6f4; font:13px sans-serif; }
            QLabel#brand { font-size:23px; font-weight:700; color:#70d6ad; letter-spacing:2px; }
            QTabWidget::pane { border:1px solid #30485f; }
            QTabBar::tab { padding:9px 20px; background:#203950; }
            QTabBar::tab:selected { border-bottom:2px solid #58b8f5; }
            QFrame#card { background:#20354a; border-radius:6px; }
        ''')
        root = QtWidgets.QWidget()
        outer = QtWidgets.QVBoxLayout(root)
        outer.setContentsMargins(18, 12, 18, 12)
        header = QtWidgets.QHBoxLayout()
        brand = QtWidgets.QLabel('BULLET VIEW')
        brand.setObjectName('brand')
        header.addWidget(brand)
        self.status = QtWidgets.QLabel('Starting MAVLink input…')
        header.addWidget(self.status, 1)
        header.addWidget(QtWidgets.QLabel(presenter.endpoint))
        outer.addLayout(header)
        self.tabs = QtWidgets.QTabWidget()
        self.telemetry_tab = QtWidgets.QWidget()
        self.parameters_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.telemetry_tab, 'Telemetry')
        self.tabs.addTab(self.parameters_tab, 'Parameters')
        outer.addWidget(self.tabs, 1)
        self._build_telemetry()
        self._build_parameters()
        self.setCentralWidget(root)
        presenter.snapshot_changed.connect(self.set_snapshot)
        presenter.status_changed.connect(self.status.setText)

    def _build_telemetry(self):
        layout = QtWidgets.QHBoxLayout(self.telemetry_tab)
        self.flight_ball = FlightBall()
        layout.addWidget(self.flight_ball, 2)
        self.altitude = AltitudeWidget()
        layout.addWidget(self.altitude, 1)
        panel = QtWidgets.QFrame()
        panel.setObjectName('card')
        details = QtWidgets.QVBoxLayout(panel)
        details.addWidget(QtWidgets.QLabel('ATTITUDE'))
        self.roll = self._value_label('Roll')
        self.pitch = self._value_label('Pitch')
        self.yaw = self._value_label('Yaw')
        for label in (self.roll, self.pitch, self.yaw):
            details.addWidget(label)
        details.addStretch(1)
        layout.addWidget(panel, 1)

    @staticmethod
    def _value_label(name):
        label = QtWidgets.QLabel(name + '\n—')
        label.setStyleSheet('padding:12px; font-size:16px; font-weight:600')
        return label

    def _build_parameters(self):
        layout = QtWidgets.QVBoxLayout(self.parameters_tab)
        message = QtWidgets.QLabel('Parameter updates are planned for v2.\n\nThis v1 viewer is receive-only.')
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet('color:#9bb0c8; font-size:16px;')
        layout.addWidget(message)

    @QtCore.Slot(object)
    def set_snapshot(self, snapshot: TelemetrySnapshot):
        self.flight_ball.set_attitude(snapshot.attitude)
        self.altitude.set_altitude(snapshot.altitude)
        if snapshot.attitude is None:
            for label, name in ((self.roll, 'Roll'), (self.pitch, 'Pitch'), (self.yaw, 'Yaw')):
                label.setText(name + '\n—')
        else:
            values = ((self.roll, 'Roll', snapshot.attitude.roll_rad),
                      (self.pitch, 'Pitch', snapshot.attitude.pitch_rad),
                      (self.yaw, 'Yaw', snapshot.attitude.yaw_rad))
            for label, name, value in values:
                label.setText(f'{name}\n{degrees(value):+.1f}°')

    def closeEvent(self, event):
        self.presenter.stop()
        event.accept()
