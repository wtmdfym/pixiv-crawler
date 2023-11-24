import os
import sys
import traceback
from PyQt6.QtCore import Qt, QFileInfo, QSize
from PyQt6.QtGui import QPixmap, QIcon, QCursor, QAction

from image_god_GUI import Ui_MainWindow as mainWindow
from webbrowser import open as open_url
from PyQt6.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QFileDialog, QAbstractItemView, \
    QMenu, QFileIconProvider, QMessageBox


class ImageGod(QMainWindow, mainWindow):
    pixRatio = 1

    def __init__(self):
        super(ImageGod, self).__init__()
        self.setupUi(self)
        self.ui_init()
        self.slot_init()

    def ui_init(self):

        self.treeWidget.setColumnCount(1)
        self.treeWidget.setColumnWidth(0, 30)
        self.treeWidget.setHeaderLabels(["目录文件"])
        self.treeWidget.setIconSize(QSize(25, 25))
        self.treeWidget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setCentralWidget(self.scrollArea)
        self.scrollArea.setWidgetResizable(True)
        self.action_broom.setEnabled(False)
        self.scrollArea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scrollArea.setGeometry(0, 0, 800, 800)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.currPixmap = QPixmap()
        self.change_action_ui(False)
        self.menu_init()

    def slot_init(self):
        self.action_addDir.triggered.connect(self.on_openDir_triggered)
        self.action_exit.triggered.connect(self.close)
        self.actionabout_author.triggered.connect(
            lambda: open_url("https://blog.csdn.net/a1397852386"))
        self.actionabout_qt.triggered.connect(
            lambda: QMessageBox.aboutQt(self, "关于QT"))
        self.action_zoomIn.triggered.connect(self.on_actionZoomIn_triggered)
        self.action_zoomOut.triggered.connect(self.on_actionZoomOut_triggered)
        self.action_zoomFit.triggered.connect(self. on_zoomFit_triggered)
        self.action_broom.triggered.connect(self.clear_dirTree)
        self.actiontree.triggered.connect(
            lambda: self.dockWidget.setVisible(self.actiontree.isChecked()))
        # self.dockWidget.closeEvent=self.actiontree.setChecked(not self.dockWidget.isVisible())
        self.treeWidget.customContextMenuRequested.connect(
            self.onTreeWidgetCustomContextMenuRequested)
        self.treeWidget.itemClicked.connect(self.onTreeItemClicked)

    def menu_init(self):
        """
        treeWidget右击菜单初始化
        :return:
        """
        self.treeWidget_menu = QMenu(self.treeWidget)
        self.action_show_image = QAction(self)  # 查看图片
        self.action_show_infos = QAction(self)  # 查看文件信息
        self.action_open_image_folder = QAction(self)  # 打开所在文件夹
        self.action_show_image.setText("查看图片")
        self.action_show_infos.setText("查看文件信息")
        self.action_open_image_folder.setText("打开所在文件夹")
        self.treeWidget_menu.addActions(
            [self.action_show_image, self.action_show_infos, self.action_open_image_folder, ])

    def on_openDir_triggered(self):
        """
        打开有图片的目录
        :return:
        """

        def CreateTree(dirs, root, path):
            """
            创建目录树
            :param dirs:
            :param root:
            :param path:
            :return:
            """
            for i in dirs:
                path_new = path + '\\' + i
                if os.path.isdir(path_new):
                    fileInfo = QFileInfo(path_new)
                    child = QTreeWidgetItem(root)
                    dirs_new = os.listdir(path_new)
                    data = ""
                    if self.check_dir(path_new):  # 确定文件夹有图片文件后，再创建子节点
                        CreateTree(dirs_new, child, path_new)

                else:
                    fileInfo = QFileInfo(path_new)
                    if not self.check_file(fileInfo.suffix()):
                        continue
                    child = QTreeWidgetItem(root)
                    data = fileInfo.absoluteFilePath()
                    # 添加其他队列
                    # child.setText(1, str(fileInfo.size()))
                    # child.setToolTip(1, str(fileInfo.size()))
                    # child.setText(2, fileInfo.suffix())
                    # child.setToolTip(2, fileInfo.suffix())
                child.setData(0, Qt.ItemDataRole.UserRole, data)
                fileIcon = QFileIconProvider()
                icon = QIcon(fileIcon.icon(fileInfo))
                child.setText(0, i)
                child.setToolTip(0, i)
                child.setIcon(0, QIcon(icon))
                child.setExpanded(False)

        path = QFileDialog.getExistingDirectory(self, "选取文件夹", "./")
        # self.treeWidget.setHeaderLabels(["目录文件", "大小", "类型", "创建时间", "上次修改时间"])
        if not path:
            return
        dirs = os.listdir(path)
        if self.check_dir(path, root=True):  # 确定文件夹有图片文件后，再创建子节点
            fileInfo = QFileInfo(path)
            fileIcon = QFileIconProvider()
            icon = QIcon(fileIcon.icon(fileInfo))
            fileName_root = QTreeWidgetItem(self.treeWidget)
            fileName_root.setText(0, fileInfo.fileName())
            fileName_root.setToolTip(0, fileInfo.fileName())
            fileName_root.setIcon(0, QIcon(icon))
            fileName_root.setData(0, Qt.ItemDataRole.UserRole, "")
            CreateTree(dirs, fileName_root, path)
            self.action_broom.setEnabled(True)
            QApplication.processEvents()
        else:
            QMessageBox.warning(self, "警告", "选择的目录不存在图片文件！")

    def clear_dirTree(self):
        """
        清空目录树
        :return:
        """
        self.treeWidget.clear()
        self.action_broom.setEnabled(False)
        self.label.setPixmap(QPixmap(""))
        self.change_action_ui(False)

    def onTreeItemClicked(self, item, column):
        """
        treeWidget节点被单击
        :return:
        """
        file = item.data(column, Qt.ItemDataRole.UserRole)
        self.show_image(file)

    def show_image(self, file):
        if file:
            self.pixRatio = 1  # 每次都重置为1
            self.statusbar.showMessage(file)  # 将文件名展示到状态栏
            self.currPixmap.load(file)
            self.on_zoomFit_triggered()
            self.change_action_ui(True)

    def show_file_infos(self, file):
        """
        文件信息
        :param file:
        :return:
        """
        infos = ""
        try:
            file_obj = QFileInfo(file)
            file_name = file_obj.fileName()
            file_size = file_obj.size()
            file_suffix = file_obj.suffix()
            file_last = file_obj.lastModified().toString()
            file_create = file_obj.created().toString()
            file_ow_id = file_obj.ownerId()
            infos = "文件名：{}\n文件类型：{}\n文件大小：{}字节\n创建时间：{}\n上次修改时间：{}\nownerId：{}".format(file_name, file_suffix,
                                                                                        file_size,
                                                                                        file_create, file_last,
                                                                                        file_ow_id)
        except:
            traceback.print_exc()
        if infos:
            QMessageBox.information(self, "文件信息", infos)
        else:
            QMessageBox.warning(self, "警告", "文件未找到")

    def onTreeWidgetCustomContextMenuRequested(self, pos):
        """
        treeWidget被右击事件
        :return:
        """
        try:
            item = self.treeWidget.currentItem()
            index = self.treeWidget.indexFromItem(item, 0).row()
            print("index===", index)
            column = self.treeWidget.currentColumn()
            item1 = self.treeWidget.itemAt(pos)
            file = item.data(column, Qt.ItemDataRole.UserRole)
            if item != None and item1 != None and file != "":
                try:
                    self.action_show_image.triggered.disconnect()
                    self.action_show_infos.triggered.disconnect()
                    self.action_open_image_folder.triggered.disconnect()
                except:
                    traceback.print_exc()
                print(item.text(column))
                print(file)
                self.action_show_image.triggered.connect(
                    lambda: self.show_image(file))
                self.action_show_infos.triggered.connect(
                    lambda: self.show_file_infos(file))
                self.action_open_image_folder.triggered.connect(
                    lambda: os.startfile(os.path.dirname(file)))
                self.treeWidget_menu.exec(QCursor.pos())
        except:
            traceback.print_exc()

    def on_zoomFit_triggered(self):
        """
        自动适应高宽
        :return:
        """
        width = self.scrollArea.width()
        height = self.scrollArea.height()
        pix = self.currPixmap.scaled(
            width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.label.setPixmap(pix)

    def on_actionZoomIn_triggered(self):
        """
        放大图片
        :return:
        """
        self.pixRatio = self.pixRatio * 1.2
        width = self.pixRatio * self.currPixmap.width()
        height = self.pixRatio * self.currPixmap.height()
        pix = self.currPixmap.scaled(int(width), int(height))
        self.label.setPixmap(pix)

    def on_actionZoomOut_triggered(self):
        """
        放大图片
        :return:
        """
        pixRatio_tmp = self.pixRatio
        self.pixRatio = self.pixRatio * 0.8
        width = self.pixRatio * self.currPixmap.width()
        height = self.pixRatio * self.currPixmap.height()
        if width < self.scrollArea.width() and height < self.scrollArea.height():  # 避免缩小太小导致失真
            self.pixRatio = pixRatio_tmp
            return
        pix = self.currPixmap.scaled(int(width), int(height))
        self.label.setPixmap(pix)

    def check_dir(self, dir, root=False):
        """
        查看文件夹是否有图片文件
        :param dir:
        :return:
        """
        for file in os.listdir(dir):
            file_abs = dir + '\\' + file
            if os.path.isdir(file_abs):
                return True
            if "." in file:
                if self.check_file(file.split(".")[-1]):
                    return True
        return False

    def check_file(self, suffix):
        """
        看文件是否为图片文件
        :param suffix:
        :return:
        """
        if suffix in ['jpg', 'png', 'jpeg', 'psd', 'bmp', 'webp']:
            return True
        else:
            return False

    def change_action_ui(self, flag):
        """
        改变按钮UI状态
        :param falg:
        :return:
        """
        self.action_zoomIn.setEnabled(flag)
        self.action_zoomOut.setEnabled(flag)
        self.action_zoomFit.setEnabled(flag)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = ImageGod()
    ui.show()
    sys.exit(app.exec())
