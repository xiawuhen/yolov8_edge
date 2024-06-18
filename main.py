from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from main_win.win5 import Ui_mainWindow
from PyQt5.QtCore import Qt, QPoint, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QImage
from PyQt5.QtNetwork import *
from utils.datasets import LoadImages, LoadWebcam
from utils.CustomMessageBox import MessageBox
import db
from dialog.rtsp_win import Window
global time_tan
import sys
import openpyxl

import json
import numpy as np
import torch
import requests

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

import os

import cv2
import datetime


class_indict={
    "1": "正常",
    "2": "未佩戴安全帽",
    "3": "未佩戴反光衣",
    "4": "未佩戴安全帽反光衣"
}
class DetThread(QThread):
    send_img = pyqtSignal(np.ndarray)
    send_msg = pyqtSignal(str)

    def __init__(self):
        super(DetThread, self).__init__()
        self.source = '0'
        self.conf_thres = 0.2
        self.iou_thres = 0.2
        self.jump_out = False
        self.is_continue = True
    @torch.no_grad()

    def run(self,
            imgsz=640,  # inference size (pixels)
            ):
        # Initialize
        try:
            if self.source.isnumeric() or self.source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://')):
                dataset = LoadWebcam(self.source, img_size=imgsz)
                # bs = len(dataset)  # batch_size
            else:
                dataset = LoadImages(self.source, img_size=imgsz)
            dataset = iter(dataset)
            while True:
                # 手动停止
                if self.jump_out:
                    self.vid_cap.release()
                    self.send_msg.emit('停止')
                    break
                # 暂停开关
                if self.is_continue:
                    path, img, im0s, self.vid_cap = next(dataset)
                    # print(type(im0s))
                    self.send_img.emit(im0s)
        except Exception as e:
            self.send_msg.emit('%s' % e)
class DetThread2(QThread):
    send_list = pyqtSignal(str)

    def __init__(self):
        super(DetThread2, self).__init__()
        self.suo = False
        self.myudpsocket = QUdpSocket()
        self.myudpsocket.bind(QHostAddress.Any, 11451)
        self.myudpsocket.readyRead.connect(self.receive_data)
        self.sv=0
        self.sh=0
        self.svh = 0
        #192.168.42.1
    def receive_data(self):
        try:
            while self.myudpsocket.hasPendingDatagrams():
                datagram, host, port = self.myudpsocket.readDatagram(self.myudpsocket.pendingDatagramSize())
                decoded_data = datagram.decode('utf-8')
                # 解析JSON数据
                json_data = json.loads(decoded_data)
                # 访问解析后的数据
                person_count = json_data['Person_count']
                classes = json_data['Calsses']
                image = json_data['Image']
                x1 = json_data['x1']
                y1 = json_data['y1']
                x2 = json_data['x2']
                y2 = json_data['y2']
                # 打印解析后的数据
                print(f"Person Count: {person_count}")
                print(f"Classes: {classes}")
                print(f"Image: {image}")
                print(f"x1: {x1}")
                print(f"y1: {y1}")
                print(f"x2: {x2}")
                print(f"y2: {y2}")
                print("Received JSON data:", datagram)

                current_time = datetime.datetime.now()
                # 准备要插入的数据
                person_count = json_data['Person_count']
                classes = json_data['Calsses']
                image = json_data['Image']

                image_ip=ip+image

                if classes==2:
                    self.sv=self.sv+1
                if classes==3:
                    self.sh=self.sh+1
                if classes==4:
                    self.svh=self.svh+1

                sql = "UPDATE records_svn SET class_num = CASE category " \
                      "WHEN '未佩戴反光衣' THEN %s " \
                      "WHEN '未佩戴安全帽' THEN %s " \
                      "WHEN '未佩戴安全帽反光衣' THEN %s " \
                      "END WHERE category IN ('未佩戴反光衣', '未佩戴安全帽', '未佩戴安全帽反光衣')" % (self.sv, self.sh, self.svh)
                db.exec_(sql)

                sql = "UPDATE records_sum SET sv = %s, sh = %s, svh = %s" % (self.sv, self.sh, self.svh)

                db.exec_(sql)

                classes_data = class_indict[str(classes)]
                current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
                s=str(current_time_str)+' '+str(classes_data)
                # self.resultWidget.addItems([s])  # 将最后的结果进行展示
                # 添加记录
                sql = "INSERT INTO records (time, person_count, classes, image) VALUES ('%s', '%s', '%s', '%s')" % (
                    current_time, person_count, classes_data , image_ip)
                db.exec_(sql)
                self.send_list.emit('%s' % s)
        except Exception as e:
            print(repr(e))
class MainWindow(QMainWindow, Ui_mainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.m_flag = False
        self.setWindowFlags(Qt.CustomizeWindowHint)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        # 自定义标题栏按钮
        self.minButton.clicked.connect(self.showMinimized)
        self.maxButton.clicked.connect(self.max_or_restore)
        self.closeButton.clicked.connect(self.close)
        self.pushButton.clicked.connect(self.excel)
        self.pushButton_2.clicked.connect(self.kai)
        self.pushButton_3.clicked.connect(self.guan)
        # yolov5线程
        self.det_thread = DetThread()
        self.det_thread2 = DetThread2()

        self.det_thread.source = '0'                                    # 默认打开本机摄像头，无需保存到配置文件，给多线程
        # 在初始化界面时将控件存储在列表中
        self.img_labels = [self.img1, self.img1_2, self.img1_3, self.img1_4]
        self.category_labels = [self.label1, self.label1_2, self.label1_3, self.label1_4]
        #当线程获取到了图片信息，emit发送信息，触发执行show_image(x, self.raw_video)   分别为emit的图像信息，和绑定槽函数的传参（标签名）
        self.det_thread.send_img.connect(lambda x: self.show_image(x, self.out_video))
        self.det_thread.send_msg.connect(lambda x: self.show_msg(x))#当线程获取到了消息，emit发送信息，展示此消息
        self.det_thread2.send_list.connect(lambda x: self.receive_data(x))  # 当线程获取到了消息，emit发送信息，展示此消息
        self.rtspButton.clicked.connect(self.chose_rtsp)  # 视频按钮
        self.runButton.clicked.connect(self.run_or_continue)#暂停
        self.stopButton.clicked.connect(self.stop)#停止
    def kai(self):
        client.send_message('LED ON')
    def guan(self):
        client.send_message('LED OFF')
    def receive_data(self,x):
        try:
            self.resultWidget.addItems([x])  # 将最后的结果进行展示
            sql = "SELECT classes, image FROM records ORDER BY id DESC LIMIT 4"  # 查询最后四行的 classes 和 image
            res = db.query(sql)
            for i, row in enumerate(res):
                # if i>0:
                classes_data = row[0]
                image_data = row[1]
                img_label = self.img_labels[i]
                category_label = self.category_labels[i]

                self.load_image(image_data, img_label,i)
                # classes_data=class_indict[str(classes_data)]
                category_label.setText(classes_data)
        except Exception as e:
            self.statistic_msg('%s' % e)
    def load_image(self, image_data, img_label,i):
        # 发送请求获取图像数据
        res = requests.get(image_data)
        # 检查响应状态码
        if res.status_code == 200:
                # 将图像数据转换为QImage对象
            img=res.content
            save_path=str(i)+'.jpg'
            with open(save_path, 'wb') as file:
                file.write(img)
            image = QImage.fromData(img)
            # 将QImage对象转换为QPixmap对象
            pixmap = QPixmap.fromImage(image)
            # 获取img_label的大小
            label_width = img_label.width()
            label_height = img_label.height()
            # 调整图像以适应img_label的大小
            scaled_pixmap = pixmap.scaled(label_width, label_height, Qt.KeepAspectRatio)
            # 设置QPixmap对象给QLabel进行显示
            img_label.setPixmap(scaled_pixmap)
            img_label.setAlignment(Qt.AlignCenter)
        else:
            print("Failed to load image.")

    def opentxt_file(self):
        fileName = QFileDialog.getExistingDirectory(self, "选取文件夹")
        if fileName:
            self.txt=fileName
            self.statistic_label.setText('保存文件地址为：'+fileName)
    def excel(self):
        try:
            self.opentxt_file()
            widgetres = []
            filename = self.txt
            filename = filename + '/违章记录.xlsx'
            wb = openpyxl.Workbook()
            ws = wb['Sheet']
            # 获取listwidget中条目数
            count = self.resultWidget.count()
            # 遍历listwidget中的内容
            for i in range(count):
                widgetres.append(self.resultWidget.item(i).text())
            print(widgetres)
            for i, item in enumerate(widgetres, 1):
                ws.cell(row=i, column=1).value = item
            wb.save(filename)
        except Exception as e:
            self.statistic_msg('%s' % e)
    def chose_rtsp(self):
        self.rtsp_window = Window()#引用另外一个界面获取网络摄像头地址
        config_file = 'config/ip.json'#存放地址的文件
        if not os.path.exists(config_file):#判断是否存在该地址，若无则创建一个
            ip = "rtsp://admin:admin888@192.168.1.67:555"
            new_config = {"ip": ip}#创建地址字典
            new_json = json.dumps(new_config, ensure_ascii=False, indent=2)#将字典类型转为json类型
            with open(config_file, 'w', encoding='utf-8') as f:#将地址写入json文件
                f.write(new_json)
        else:
            config = json.load(open(config_file, 'r', encoding='utf-8'))#从json文件中加载路径，json.loads将字符串转为Python对象
            ip = config['ip']#获取到该文件中的地址
        self.rtsp_window.rtspEdit.setText(ip)#在界面中的行编辑框显示
        self.rtsp_window.show()#进行展示
        self.rtsp_window.rtspButton.clicked.connect(lambda: self.load_rtsp(self.rtsp_window.rtspEdit.text()))#如果按下了按钮，则获取该行编辑，并转入槽函数
    def load_rtsp(self, ip):
        try:
            self.stop()#暂停检测
            MessageBox(
                self.closeButton, title='提示', text='请稍等，正在加载rtsp视频流', time=1000, auto=True).exec_()
            self.det_thread.source = ip#此时更改资源，视频流的形式
            new_config = {"ip": ip}
            new_json = json.dumps(new_config, ensure_ascii=False, indent=2)#将字典类型转为json类型
            with open('config/ip.json', 'w', encoding='utf-8') as f:
                f.write(new_json)#将用户输入网络流地址写入
            self.statistic_msg('加载rtsp：{}'.format(ip))#提示框提醒
            self.rtsp_window.close()#关闭视频流界面
        except Exception as e:
            self.statistic_msg('%s' % e)
    def statistic_msg(self, msg):
        self.statistic_label.setText(msg)
    def show_msg(self, msg):
        self.runButton.setChecked(Qt.Unchecked)#未开启三态模式设置选中状态，默认为未选中，true为选中  Qt.Unchecked为未选中
        self.statistic_msg(msg)#进行展示
    def max_or_restore(self):#界面放大
        if self.maxButton.isChecked():
            self.showFullScreen()
        else:
            self.showNormal()
    # 继续/暂停
    def run_or_continue(self):
        self.det_thread.jump_out = False
        if self.runButton.isChecked():
            self.det_thread.is_continue = True
            if not self.det_thread.isRunning():
                self.det_thread.start()
                self.det_thread2.start()
            source = os.path.basename(self.det_thread.source)
            source = '摄像头设备' if source.isnumeric() else source    #source.isnumeric()：如果字符串中只包含数字字符，则返回 True，否则返回 False
        else:
            self.det_thread.is_continue = False
            self.statistic_msg('暂停')
    # 退出检测循环
    def stop(self):
        self.det_thread.jump_out = True
        self.out_video.clear()
    def send_suo(self):
        self.det_thread2.suo = True
    def mousePressEvent(self, event):
        self.m_Position = event.pos()
        if event.button() == Qt.LeftButton:
            if 0 < self.m_Position.x() < self.groupBox.pos().x() + self.groupBox.width() and \
                    0 < self.m_Position.y() < self.groupBox.pos().y() + self.groupBox.height():
                self.m_flag = True

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)  # 更改窗口位置
            # QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_flag = False
        # self.setCursor(QCursor(Qt.ArrowCursor))

    @staticmethod
    def show_image(img_src, label):
        try:
            ih, iw, _ = img_src.shape
            w = label.geometry().width()
            h = label.geometry().height()
            # 保持纵横比
            # 找出长边
            if iw > ih:
                scal = w / iw
                nw = w
                nh = int(scal * ih)
                img_src_ = cv2.resize(img_src, (nw, nh))

            else:
                scal = h / ih
                nw = int(scal * iw)
                nh = h
                img_src_ = cv2.resize(img_src, (nw, nh))
            frame = cv2.cvtColor(img_src_, cv2.COLOR_BGR2RGB)

            img = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[2] * frame.shape[1],
                         QImage.Format_RGB888)#转化为qt格式
            label.setPixmap(QPixmap.fromImage(img))#QPixmap.fromImage(img)：将Qimage图片转化为QPixmap

        except Exception as e:
            print(repr(e))

    def closeEvent(self, event):
        # 如果摄像头开着，先把摄像头关了再退出，否则极大可能可能导致检测线程未退出
        self.det_thread.jump_out = True
        MessageBox(
            self.closeButton, title='提示', text='请稍等，正在关闭程序。。。', time=2000, auto=True).exec_()
        sys.exit(0)

class UdpClient:
    def __init__(self, target_ip, target_port):
        self.udp_socket = QUdpSocket()
        self.target_ip = target_ip
        self.target_port = target_port

    def send_message(self, message):
        data = message.encode('utf-8')
        self.udp_socket.writeDatagram(data, QHostAddress(self.target_ip), self.target_port)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ip = 'http://192.168.1.101:8000/'
    # 指定目标 IP 和端口
    target_ip = "192.168.1.101"  # 本地 IP 地址，替换为目标 IP 地址
    target_port = 11451  # 目标端口，替换为目标端口

    client = UdpClient(target_ip, target_port)
    myWin = MainWindow()
    myWin.show()

    sys.exit(app.exec_())
