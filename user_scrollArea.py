from PyQt6.QtWidgets import (QWidget, QSlider, QLineEdit, QLabel, QPushButton, QScrollArea,QApplication,
                             QHBoxLayout, QVBoxLayout, QMainWindow)
from PyQt6.QtCore import Qt, QSize
from PyQt6 import QtWidgets, uic, QtGui
import sys


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.scrollarea = QScrollArea()             # Scroll Area which contains the widgets, set as the centralWidget
        self.widget = QWidget()                 # Widget that contains the collection of Vertical Box
        self.vbox = QVBoxLayout()               # The Vertical Box that contains the Horizontal Boxes of  labels and buttons

        import os
        self.img_width = 240
        self.img_height= 320
        self.images = []
        for root, dirs, files in os.walk(r'D:\nice\爬虫\img', topdown=False, onerror=None, followlinks=False):
            for name in files:
                self.images.append(os.path.join(root, name))
        #print(len(self.images))
        for i in range(len(self.images)//2):
            layout = QHBoxLayout()
            label = QLabel('Userinfo')
            label.setFixedSize(self.img_width,self.img_height)
            layout.addWidget(label)
            for j in range(2):
                label = QLabel()
                # 设置对齐方式
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # QSS Qt StyleSheet
                label.setStyleSheet('QLabel{margin:5px};')
                # 设置与宽高
                label.setFixedSize(self.img_width,self.img_height)
                # 显示图片
                label.setPixmap(self.load_image(self.images[i]))
                layout.addWidget(label)
            #self.vbox.addWidget(label)
            self.vbox.addLayout(layout)

        self.widget.setLayout(self.vbox)

        #Scroll Area Properties
        self.scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollarea.setWidgetResizable(True)
        self.scrollarea.setWidget(self.widget)
        self.scrollarea.verticalScrollBar().valueChanged.connect(self.stream_load)

        self.setCentralWidget(self.scrollarea)

        self.setGeometry(600, 100, 500, 500)
        self.setWindowTitle('Scroll Area Demonstration')
        self.show()

        return

    def load_image(self,path):
        image= QtGui.QImage(path)
        image = image.scaled(self.img_width, self.img_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pixmap=QtGui.QPixmap()
        if pixmap.convertFromImage(image):
            return pixmap
        else:return None

    def stream_load(self):
        if self.scrollarea.verticalScrollBar().value() == self.scrollarea.verticalScrollBar().maximum():
            print('Loading...')

            for datas in self.images:
                layout = QHBoxLayout()
                label = QLabel('Userinfo')
                label.setFixedSize(self.img_width,self.img_height)
                layout.addWidget(label)
                for j in range(2):
                    label = QLabel()
                    # 设置对齐方式
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    # QSS Qt StyleSheet
                    label.setStyleSheet('QLabel{margin:5px};')
                    # 设置与宽高
                    label.setFixedSize(self.img_width,self.img_height)
                    # 显示图片
                    label.setPixmap(self.load_image(datas))
                    layout.addWidget(label)
                self.vbox.addLayout(layout)
            
class ScrollArea(QScrollArea):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.widget0 = QWidget()                 # Widget that contains the collection of Vertical Box
        self.vbox = QVBoxLayout()               # The Vertical Box that contains the Horizontal Boxes of  labels and buttons

        import os
        self.img_width = 240
        self.img_height= 320
        self.images = []
        for root, dirs, files in os.walk(r'D:\nice\爬虫\img', topdown=False, onerror=None, followlinks=False):
            for name in files:
                self.images.append(os.path.join(root, name))
        #print(len(self.images))
        for i in range(len(self.images)//2):
            layout = QHBoxLayout()
            label = QLabel('Userinfo')
            label.setFixedSize(self.img_width,self.img_height)
            layout.addWidget(label)
            for j in range(2):
                label = QLabel()
                # 设置对齐方式
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # QSS Qt StyleSheet
                label.setStyleSheet('QLabel{margin:5px};')
                # 设置与宽高
                label.setFixedSize(self.img_width,self.img_height)
                # 显示图片
                label.setPixmap(self.load_image(self.images[i]))
                layout.addWidget(label)
            self.vbox.addLayout(layout)

        self.widget0.setLayout(self.vbox)

        #Scroll Area Properties
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.widget0)
        self.verticalScrollBar().valueChanged.connect(self.stream_load)

        return

    def load_image(self,path):
        image= QtGui.QImage(path)
        image = image.scaled(self.img_width, self.img_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pixmap=QtGui.QPixmap()
        if pixmap.convertFromImage(image):
            return pixmap
        else:return

    def stream_load(self):
        if self.verticalScrollBar().value() == self.verticalScrollBar().maximum():
            print('Loading...')

            for datas in self.images:
                layout = QHBoxLayout()
                label = QLabel('Userinfo')
                label.setFixedSize(self.img_width,self.img_height)
                layout.addWidget(label)
                for j in range(2):
                    label = QLabel()
                    # 设置对齐方式
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    # QSS Qt StyleSheet
                    label.setStyleSheet('QLabel{margin:5px};')
                    # 设置与宽高
                    label.setFixedSize(self.img_width,self.img_height)
                    # 显示图片
                    label.setPixmap(self.load_image(datas))
                    layout.addWidget(label)
                self.vbox.addLayout(layout)


def main():
    app = QtWidgets.QApplication(sys.argv)
    #main = MainWindow()
    scrollarea = ScrollArea()
    example = QMainWindow()
    example.setCentralWidget(scrollarea)
    example.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()