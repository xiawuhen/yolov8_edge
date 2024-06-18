from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap, QIcon


# 单按钮对话框，出现到指定时长后自动消失

'''
第一个参数是父控件指针
第二个参数是标题
第三个参数是内容
第四个参数是窗口里面要多少个按钮（默认为OK）
第五个参数指定按下Enter时使用的按钮。（默认为NoButton，此时QMessageBox会自动选择合适的默认值。）
'''
class MessageBox(QMessageBox):
    def __init__(self, *args, title='提示', count=1, time=1000, auto=False, **kwargs):
        super(MessageBox, self).__init__(*args, **kwargs)
        self._count = count
        #print(count)
        #print(title)
        self._time = time
        self._auto = auto  # 是否自动关闭
        assert count > 0  # 必须大于0
        assert time >= 500  # 必须>=500毫秒
        self.setStyleSheet('''
                            QDialog{background:rgb(75, 75, 75);
                                    color:white;}
                            QLabel{color:white;
                                    background: rgb(75, 75, 75);
                                    font-size: 15px;
                                    font-weight: light;
                                    color:white;}''')

        self.setWindowTitle(title)
        self.setIconPixmap(QPixmap(":/img/icon/笑脸.png"))

        self.setStandardButtons(self.Close)  # 关闭按钮
        self.closeBtn = self.button(self.Close)  # 获取关闭按钮
        self.closeBtn.setText('关闭')
        self.closeBtn.setVisible(False)
        self._timer = QTimer(self, timeout=self.doCountDown)
        self._timer.start(self._time)

    def doCountDown(self):
        # self.closeBtn.setText('关闭(%s)' % self._count)
        self._count -= 1
        if self._count <= 0:
            # self.closeBtn.setText('关闭')
            # self.closeBtn.setEnabled(True)
            self._timer.stop()
            if self._auto:  # 自动关闭
                self.accept()
                self.close()


if __name__ == '__main__':
    MessageBox(QWidget=None, text='123', auto=True).exec_()
