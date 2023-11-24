# -*- coding: utf-8 -*-

'''
    【简介】
	PyQT5中单元格改变每行单元格显示的图标大小例子


'''

import sys,os
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


class Table(QWidget):
    def __init__(self):
        super().__init__()
        # 设置图片宽高
        self.img_width = 240
        self.img_height= 320
        # 设置行数和列数
        self.rows = 2
        self.columns = 4
        self.pagesize = self.rows*self.columns
        self.initUI()
 
    def initUI(self):
        # 设置定位和左上角坐标
        self.setGeometry(300, 300, 900, 600)
        # 设置窗口标题
        self.setWindowTitle('QTableWidget扩展表格的单元格放置控件 的演示')
        # 设置窗口图标
        # self.setWindowIcon(QIcon('../web.ico'))
        
 
        layout = QHBoxLayout()
        self.tablewidget = QTableWidget()
        
        self.tablewidget.setRowCount(self.rows)
        self.tablewidget.setColumnCount(self.columns)
        # 设置单元格宽高
        for i in range(self.rows):  # 让行高和图片相同
            self.tablewidget.setRowHeight(i, self.img_height)
        for i in range(self.columns):  # 让列宽和图片相同
            self.tablewidget.setColumnWidth(i, self.img_width)
 
        layout.addWidget(self.tablewidget)
 
        '''
        nameItem = QTableWidgetItem('小明')
        tablewidget.setItem(0,0,nameItem)
 
        # 添加下拉列表框
        combox = QComboBox()
        combox.addItem('男')
        combox.addItem('女')
        # QSS Qt StyleSheet
        combox.setStyleSheet('QComboBox{margin:3px};')
        tablewidget.setCellWidget(0,1,combox)
 
        # 添加一个修改按钮
        modifyButton = QPushButton('修改')
        modifyButton.setDown(True)
        modifyButton.setStyleSheet('QPushButton{margin:3px};')
        tablewidget.setCellWidget(0,2,modifyButton)
        '''
        # 获取图片列表
        images = []
        for root, dirs, files in os.walk(r'D:\nice\爬虫\img', topdown=False, onerror=None, followlinks=False):
            for name in files:
                images.append(os.path.join(root, name))
                pass
                #print(os.path.join(root, name))
            for name in dirs:
                pass
                #print(os.path.join(root, name))

        # 添加标签
        for i in range(self.rows):
            for j in range(self.columns):
                label = QLabel()
                # 设置对齐方式
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # QSS Qt StyleSheet
                label.setStyleSheet('QLabel{margin:5px};')
                # 设置与宽高
                label.setFixedSize(self.img_width,self.img_height)
                # 显示图片
                label.setPixmap(self.load_image(images[i*self.columns+j]))
                # 添加到tablewidget
                self.tablewidget.setCellWidget(i,j,label)

        # 禁止编辑
        self.tablewidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
 
        # 整行选择
        # tablewidget.setSelectionBehavior(QAbstractItemView.SelectRows)
 
        # 根据内容自动调整列合行
        # tablewidget.resizeColumnsToContents()
        # tablewidget.resizeRowsToContents()
 
        # 自定义表头和第一列，隐藏显示
        self.tablewidget.horizontalHeader().setVisible(False)
        self.tablewidget.verticalHeader().setVisible(False)
 
        # 自定义第一列内容
        # tablewidget.setVerticalHeaderLabels(["a","b","c"])
 
        # 隐藏表格线
        # tablewidget.setShowGrid(False)
 
        pushbutton = QPushButton("update")
        pushbutton.clicked.connect(self.update_image)
        layout.addWidget(pushbutton)
        self.setLayout(layout)
 
        # self.listwidget.itemClicked.connect(self.clicked)
        #
        # self.setCentralWidget(self.listwidget)

    def load_image(self,path):
        image= QImage(path)
        #print(image.size())
        image = image.scaled(self.img_width, self.img_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        #print(image.size())
        pixmap=QPixmap()
        if pixmap.convertFromImage(image):
            return pixmap
        else:return None

    def update_image(self):
        images = self.image_datas[(self.page-1)*self.pagesize:self.page*self.pagesize]
        for i in range(self.rows):
            for j in range(self.columns):
                label = self.tablewidget.cellWidget(i,j)
                l = QLabel()
                l.setPixmap
                label.setPixmap(self.load_image(r'D:\nice\爬虫\100008184_p0.jpg'))

class Table2(QTableWidget):
    def __init__(self):
        super().__init__()
        # 设置图片宽高
        self.img_width = 240
        self.img_height= 320
        # 设置行数和列数
        self.rows = 2
        self.columns = 4
        self.pagesize = self.rows*self.columns
        self.page = 1
        self.initUI()
 
    def initUI(self):
        self.setRowCount(self.rows)
        self.setColumnCount(self.columns)
        # 设置单元格宽高
        for i in range(self.rows):  # 让行高和图片相同
            self.setRowHeight(i, self.img_height)
        for i in range(self.columns):  # 让列宽和图片相同
            self.setColumnWidth(i, self.img_width)
 
        '''
        # 添加一个修改按钮
        modifyButton = QPushButton('修改')
        modifyButton.setDown(True)
        modifyButton.setStyleSheet('QPushButton{margin:3px};')
        setCellWidget(0,2,modifyButton)
        '''
        # 获取图片列表
        images = []
        for root, dirs, files in os.walk(r'D:\nice\爬虫\img', topdown=False, onerror=None, followlinks=False):
            for name in files:
                images.append(os.path.join(root, name))

        # 添加标签
        for i in range(self.rows):
            for j in range(self.columns):
                label = QLabel()
                # 设置对齐方式
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # QSS Qt StyleSheet
                label.setStyleSheet('QLabel{margin:5px};')
                # 设置与宽高
                label.setFixedSize(self.img_width,self.img_height)
                # 显示图片
                label.setPixmap(self.load_image(images[i*self.columns+j]))
                # 添加到tablewidget
                self.setCellWidget(i,j,label)

        # 禁止编辑
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
 
        # 根据内容自动调整列合行
        # resizeColumnsToContents()
        # resizeRowsToContents()
 
        # 自定义表头和第一列，隐藏显示
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
 
        # 隐藏表格线
        # setShowGrid(False)
 
        # self.listwidget.itemClicked.connect(self.clicked)
        #
        # self.setCentralWidget(self.listwidget)

    def load_image(self,path):
        image= QImage(path)
        image = image.scaled(self.img_width, self.img_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        pixmap=QPixmap()
        if pixmap.convertFromImage(image):
            return pixmap
        else:return None

    def update_image(self):
        images = self.image_datas[(self.page-1)*self.pagesize:self.page*self.pagesize]
        for i in range(self.rows):
            for j in range(self.columns):
                label = self.cellWidget(i,j)
                l = QLabel()
                l.setPixmap
                label.setPixmap(self.load_image(r'D:\nice\爬虫\100008184_p0.jpg'))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    #example = Table()
    layout = QHBoxLayout()
    table = Table2()
    layout.addWidget(table)
    pushbutton = QPushButton("update")
    pushbutton.clicked.connect(table.update_image)
    layout.addWidget(pushbutton)
    example = QWidget()
    example.setLayout(layout)
    example.show()
    sys.exit(app.exec())

