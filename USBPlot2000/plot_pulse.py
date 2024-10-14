# import os
# import sys
# sys.path.insert(0, os.getcwd())

import csv
import multiprocessing
import sys
import time

import pyqtgraph as pg
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtWidgets import QMessageBox
from pyqtgraph.Qt import QtCore

import lib.usb_get as usb_get
from lib.ui import Ui_Form


class PLOT_3D(QtWidgets.QWidget, Ui_Form):
    data = {i: [] for i in range(0, 32)} # 设置全局变量 显示长度


    def __init__(self):
        super().__init__()

        self.setupUi(self)
        self.setWindowIcon(QIcon('lib/image.png'))


        # 设置串口实例
        self.com = QSerialPort()
        self.port_check()

        self.init() #界面按钮初始化

        # 绘图部件
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')




        #graph data1
        self.pw = [0] *32
        self.curve = [0] *32

        for i in range(32):

            self.pw[i] = pg.GraphicsLayoutWidget(show=True)
            p1 = self.pw[i].addPlot()
            self.curve[i] = p1.plot(PLOT_3D.data[i],pen='r',name='DATA1')
            exec(f"self.Layout_graph_{i+1}.addWidget(self.pw[{i}])",)
            #self.Layout_graph_1.addWidget(self.pw[0])  # 添加绘图部件到网格布局层



    """定义信号与槽"""

    def init(self):
        # 打开按钮
        self.open_button.clicked.connect(self.port_open)
        # 关闭按钮
        self.close_button.clicked.connect(self.port_close)

        # 清空
        self.start_measure_button.clicked.connect(self.start_measure)

        # 保存数据
        self.savedata_button.clicked.connect(self.save_data_button)

        # 退出应用
        self.quit_Button.clicked.connect(self.quit)


    # 串口检测
    def port_check(self):
        # 检测所有存在的串口，将信息存储在字典中
        self.serialportnum.clear()
        port_list = QSerialPortInfo.availablePorts()
        # print(self.port_list)
        if len(port_list) == 0:
            pass
            #self.state_label.setText("None")
        else:
            for port in port_list:
                self.com.setPort(port)
                if self.com.open(QSerialPort.ReadWrite):
                    self.serialportnum.addItem('    ' + port.portName())
                    self.com.close()

    # 打开串口
    def port_open(self):
        if self.serialportnum.currentText().strip() == 'None':
            QMessageBox.critical(self, "Port Error", "请选择串口！")
            return None
        print(self.serialportnum.currentText().strip())
        print("开始")

        #初始化数据读取，接收
        self.usbdata = usb_get.USB_DataDecode(self.serialportnum.currentText().strip())
        self.sensor = []

        # 接收进程数据
        self.value_list = {i: [0]*2000 for i in range(0, 32)}
        self.read_queue()
        self.getdata = QtCore.QTimer()
        self.getdata.timeout.connect(self.read_queue)
        self.getdata.start(10)


        #画图多线程中断
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(10)





        self.timer_save = QtCore.QTimer() 
        self.timer_save.timeout.connect(self.save_timer)


    def start_measure(self):
        print("清空")
        self.sensor = []
        self.value_list = {i: [0] * 200 for i in range(0, 32)}


    def port_close(self):
        self.usbdata.GUI_order.put('stop')  # 发送结束
        self.timer_save.stop()  # 停止
        self.sensor = []
        self.textBrowser_3.append("已停止")  # 在指定的区域显示提示信息
        print("已停止")


    def save_data(self):
        pass
        print("保存成功")

    def save_data_button(self):
        button_state = self.savedata_button.text()
        int_time = time.strftime("%Y年%m月%d日 %H时%M分%S秒", time.localtime())
        self.savepath =  './lib/data_save/' + int_time + '_sensor.csv'


        if (button_state == 'Start Save'):
            self.save_data_init(self.savepath)
            self.savedata_button.setText("Complete save")
            self.clear_Queue(self.usbdata.data_out)  # 清空队列
            self.usbdata.GUI_order.put('start')  # 发送开始
            self.textBrowser_3.append("开始检测")  # 在指定的区域显示提示信息
            self.timer_save.start(10)     #定时保存时间 ms

        else:
            self.usbdata.GUI_order.put('stop')  # 发送结束
            self.timer_save.stop()  # 停止
            self.textBrowser_2.append("保存成功")  # 在指定的区域显示提示信息
            self.textBrowser_3.append("保存结束")  # 在指定的区域显示提示信息
            self.savedata_button.setText("Start Save")



    def quit(self):
        try:
            self.usbdata.close_usb()
        except:
            pass
        app.quit()
        print("成功退出")


    def save_data_init(self, filenname):
        data_head = ['timestamp'] + ['sensor' + str(i) for i in range(1, 33)]
        headers =   data_head
        with open(filenname, 'w', newline='') as form:
            writer = csv.writer(form)
            writer.writerow(headers)

    def write_data(self, data):
        filenname = self.savepath
        with open(filenname, 'a', newline='') as form:
            writer = csv.writer(form)
            writer.writerows(data)
        self.sensor = []

    def save_timer(self):
        # 计时显示
        buf_len = len(self.sensor)
        int_time = time.strftime("%Y-%m-%d- %H:%M:%S", time.localtime())

        self.textBrowser_2.append(int_time)  # 在指定的区域显示提示信息

        res = []
        while self.usbdata.data_out.qsize() > 0:
            res.append(self.usbdata.data_out.get())


        #res.reverse()
        self.sensor = self.sensor + res
        if (buf_len >= 20):
            print('Saving')
            self.write_data(self.sensor)





    def clear_Queue(self,q):
        res = []
        while q.qsize() > 0:
            res.append(q.get())
        self.value_list = {i: [0] * 200 for i in range(0, 32)}



    # 绘图
    def read_queue(self):
        while self.usbdata.data_z.qsize() > 0:
            self.get_value = self.usbdata.data_z.get(True)

            for i in range(32):
                self.value_list[i][:-1] = self.value_list[i][1:]  # shift data in the array one sample left
                self.value_list[i][-1] = self.get_value[i]

        print(self.usbdata.data_z.qsize())


    #绘图
    def update_plot(self):



        #波形显示：
        for i in range(32):
            self.curve[i].setData(self.value_list[i])
        # self.curve2.setData(self.value_list[1])
        # self.curve3.setData(self.value_list[2])
        # self.curve4.setData(self.value_list[3])
        # self.curve5.setData(self.value_list[4])
        # self.curve6.setData(self.value_list[5])
        # self.curve7.setData(self.value_list[6])
        # self.curve8.setData(self.value_list[7])
        #

        #3D绘图可视化
        #z = pg.gaussianFilter(z,(4,4))   #高斯平滑

        #显示第一个数值

def closehand():
    print('close')



if __name__ == '__main__':

    multiprocessing.freeze_support()

    app = QtWidgets.QApplication(sys.argv)
    window = PLOT_3D()
    window.show()
    sys.exit(app.exec_())



