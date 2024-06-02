import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
import serial
from serial.tools import list_ports

ser = None
ser_flag = False
ser_init = False

class Graph(QWidget):
    def __init__(self, title, background_color, pen_color, data, x_data):
        super().__init__()

        self.x_data = x_data
        self.data = data

        self.graph = pg.PlotWidget(title=title)
        self.graph.setBackground(background_color)
        self.graph.showGrid(x=True, y=True)
        self.graph.setMouseEnabled(x=False, y=False)
        self.graph.setAntialiasing(True)

        pen = pg.mkPen(color=pen_color, width=1)

        self.curve = self.graph.plot(pen=pen)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)

        layout = QVBoxLayout()
        layout.addWidget(self.graph)
        self.setLayout(layout)

    def update_plot(self):
        self.curve.setData(self.x_data, self.data)

class Launch_Command(QWidget):
    def __init__(self, count_down_label):
        super().__init__()
        self.count_down_label = count_down_label

        self.correct_password = "TUSI-2024-05-11"

        self.setStyleSheet("background-color: #252525;")

        self.groupbox = QGroupBox("Ignite_Command")
        self.groupbox.setStyleSheet("QGroupBox:title { color: white; subcontrol-origin: margin; padding: -2px; }")

        self.count_down = QLabel("Set CountDown")
        self.count_down.setStyleSheet("color: white;")

        self.spinbox = QSpinBox()
        self.spinbox.setStyleSheet("color: white; background-color: #161616; border: 0px;")
        self.spinbox.setMinimum(0)
        self.spinbox.setMaximum(10)

        self.count_down_setting_layout = QHBoxLayout()
        self.count_down_setting_layout.addWidget(self.count_down)
        self.count_down_setting_layout.addWidget(self.spinbox)

        self.password = QLineEdit()
        self.password.setStyleSheet("color: white; background-color: #161616; border: 0px;")

        self.launchBtn = QPushButton("Ignite!")
        self.launchBtn.setStyleSheet("QPushButton {color: white; background-color: #E22239; height: 40px;}" "QPushButton::pressed {background-color:#D42035; border: 2px solid #D42035; }")
        self.launchBtn.clicked.connect(self.ignite)

        group_layout = QVBoxLayout()
        group_layout.addLayout(self.count_down_setting_layout)
        group_layout.addWidget(self.password)
        group_layout.addWidget(self.launchBtn)

        self.groupbox.setLayout(group_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.groupbox)

        self.setLayout(layout)

    def ignite(self):
        if self.password.text() != self.correct_password:
            msg = QMessageBox()
            msg.setWindowTitle("wrong password")
            msg.setText("please enter correct password")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        self.timer = QTimer()
        self.cnt = self.spinbox.value()
        self.timer.timeout.connect(self.updateTimer)
        self.timer.start(1000)

    def updateTimer(self):
        print(self.cnt)
        self.cnt-=1
        self.count_down_label.setText("T- 00 : 00: "+'{:02d}'.format(self.cnt+1))
        if self.cnt == -1:
            self.timer.stop()

class Serial_Connect(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("background-color: #252525;")

        self.groupbox = QGroupBox("Serial_Connect")
        self.groupbox.setStyleSheet("QGroupBox:title { color: white; subcontrol-origin: margin; padding: -2px; }")

        self.port_label = QLabel("Port")
        self.port_label.setStyleSheet("color: white;")

        self.port_list_combobox = QComboBox()
        self.port_list_combobox.setStyleSheet("color: white; background-color: #161616;")
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setStyleSheet("QPushButton {color: white; background-color: #1B78F2;}" "QPushButton::pressed {background-color:#1B78F2; border: 2px solid #1B78F2; }")
        self.connect_btn.clicked.connect(self.port_connect)

        self.connect_setting_layout = QHBoxLayout()
        self.connect_setting_layout.addWidget(self.port_list_combobox)
        self.connect_setting_layout.addWidget(self.connect_btn)

        self.connect_state_label = QLabel("Connect State: ")
        self.connect_state_label.setStyleSheet("color: white;")
        self.port_state_label = QLabel("disconnected")
        self.port_state_label.setStyleSheet("color: red;")
        

        self.connect_state_layout = QHBoxLayout()
        self.connect_state_layout.addWidget(self.connect_state_label)
        self.connect_state_layout.addWidget(self.port_state_label)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setStyleSheet("QPushButton {color: white; background-color: #161616;}" "QPushButton::pressed {background-color:#1B78F2; border: 2px solid #1B78F2; }")
        self.disconnect_btn.clicked.connect(self.port_disconnect)

        group_layout = QVBoxLayout()

        group_layout.addWidget(self.port_label)
        group_layout.addLayout(self.connect_setting_layout)
        group_layout.addLayout(self.connect_state_layout)
        group_layout.addWidget(self.disconnect_btn)

        self.groupbox.setLayout(group_layout)

        layout = QVBoxLayout()
        layout.addWidget(self.groupbox)

        self.setLayout(layout)

        self.port_setting()

    def port_setting(self):
        current_ports = [self.port_list_combobox.itemText(i) for i in range(self.port_list_combobox.count())]
        available_ports = [port.device for port in list_ports.comports()]
        if available_ports != current_ports:
            self.port_list_combobox.clear()
            self.port_list_combobox.addItems(available_ports)
    
    def port_connect(self):
        global ser
        global ser_flag
        global ser_init
        ser = serial.Serial(port=self.port_list_combobox.currentText(),baudrate=9600,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS,timeout=1)
        self.port_state_label.setText("connected")
        self.port_state_label.setStyleSheet("color: green;")
        ser_flag = True
        ser_init = True
    def port_disconnect(self):
        global ser
        global ser_flag
        self.port_state_label.setText("disconnected")
        self.port_state_label.setStyleSheet("color: red;")
        ser.close()
        ser = None
        ser_flag = False

        
class DAQ_VALUE(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #252525;")

        self.Timer_label = QLabel("T- -- : -- : --")
        self.Timer_label.setStyleSheet("color: white;")
        self.Timer_label.setFont(QFont('Arial', 30)) 
        self.Timer_label.setAlignment(QtCore.Qt.AlignCenter)

        self.current_thrust_lable = QLabel("Thrust: ")
        self.current_thrust_lable.setStyleSheet("color: white;")
        self.current_thrust_lable.setFont(QFont('Arial', 20)) 

        self.current_thrust_value_lable = QLabel("-")
        self.current_thrust_value_lable.setStyleSheet("color: white;")
        self.current_thrust_value_lable.setFont(QFont('Arial', 20)) 

        self.logo_label = QLabel()
        pixmap = QPixmap("img/logo_white.png")
        # 이미지의 크기를 반으로 줄입니다.
        scaled_pixmap = pixmap.scaled(70, 70)
        self.logo_label.setPixmap(scaled_pixmap)
        self.logo_label.setAlignment(QtCore.Qt.AlignCenter)

        self.current_pressure_lable = QLabel("Pressure: ")
        self.current_pressure_lable.setStyleSheet("color: white;")
        self.current_pressure_lable.setFont(QFont('Arial', 20)) 

        self.current_pressure_value_lable = QLabel("-")
        self.current_pressure_value_lable.setStyleSheet("color: white;")
        self.current_pressure_value_lable.setFont(QFont('Arial', 20)) 

        self.thrust_value_layout = QHBoxLayout()
        self.thrust_value_layout.addWidget(self.current_thrust_lable)
        self.thrust_value_layout.addWidget(self.current_thrust_value_lable)
        self.thrust_value_layout.addStretch(1)
        self.thrust_value_layout.addWidget(self.current_pressure_lable)
        self.thrust_value_layout.addWidget(self.current_pressure_value_lable)

        self.thrust_value_layout.setAlignment(QtCore.Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.Timer_label)
        layout.addWidget(self.logo_label)
        layout.addLayout(self.thrust_value_layout)

        self.setLayout(layout)



class MainWindow(QMainWindow):
    
    def __init__(self):
        self.data_len = 0
        super().__init__()

        #메인 윈도우 세팅
        self.setWindowTitle("TUSI TMS DAQ SYSTEM")

        self.setWindowIcon(QIcon("img/logo.png"))
        self.setMinimumSize(980,720)

        self.setStyleSheet("background-color: #161616;")

        #그래프 세팅
        self.data = []
        self.x_data = []

        self.data2 = []
        self.x_data2 = []
        
        self.thrust_graph = Graph("Thrust", '#252525', "#7E49F2", self.data, self.x_data)
        self.pressure_graph = Graph("Pressure", '#252525', "#3FA194", self.data2, self.x_data2)

        # 타이머 세팅
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(0.10416666666666667129)

        # 그래프 업데이트

        # 하단 설정바
        bottom_group = QGroupBox()
        bottom_group.setStyleSheet("background-color: #252525;")

        bottom_layout = QHBoxLayout()
        serial_layout = Serial_Connect()
        self.daqvalue_layout = DAQ_VALUE()
        launch_layout = Launch_Command(self.daqvalue_layout.Timer_label)

        bottom_layout.addWidget(serial_layout)
        bottom_layout.addWidget(self.daqvalue_layout)
        bottom_layout.addWidget(launch_layout)
        bottom_layout.setStretchFactor(serial_layout, 1)
        bottom_layout.setStretchFactor(self.daqvalue_layout, 1)
        bottom_layout.setStretchFactor(launch_layout, 1)

        bottom_group.setLayout(bottom_layout)

        bottom_final_layout = QVBoxLayout()
        bottom_final_layout.addWidget(bottom_group)

        #그래프 레이아웃 세팅
        graph_layout = QHBoxLayout()
        graph_layout.addWidget(self.thrust_graph)
        graph_layout.addWidget(self.pressure_graph)

        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.addLayout(graph_layout)
        main_layout.addLayout(bottom_final_layout)
        
        self.setCentralWidget(widget)

    def update_plot(self):
        global ser
        global ser_init
        thrust_value = None
        pressure_value = None
        
        if ser_init == False:
            return
        
        if ser == None:
            self.data.append(0)
            self.data2.append(0)
            thrust_value = 0
            pressure_value = 0
        else:
            try:
                received_data = ser.readline().decode().strip()
                data_list = received_data.split(",")
                self.data.append(float(data_list[0]))
                self.data2.append(float(data_list[1]))
                thrust_value = float(data_list[0])
                pressure_value = float(data_list[1])
            except:
                self.data.append(0)
                self.data2.append(0)

        self.x_data.append(self.data_len)
        self.x_data2.append(self.data_len)

        self.data_len+=1

        self.daqvalue_layout.current_thrust_value_lable.setText(str(thrust_value))
        self.daqvalue_layout.current_pressure_value_lable.setText(str(pressure_value))

        if len(self.data)>=1000:
            del self.data[0]
            del self.x_data[0]

            del self.data2[0]
            del self.x_data2[0]


app = QApplication(sys.argv)
win = MainWindow()
win.showMaximized()
app.exec_()