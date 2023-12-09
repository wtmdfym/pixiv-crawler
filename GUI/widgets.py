# -*-coding:utf-8-*-
import os
import re
from PyQt6.QtCore import (
    QSortFilterProxyModel,
    Qt,
    pyqtSlot,
    QThreadPool,
    QPoint,
)
from PyQt6.QtGui import QImage, QPixmap, QPainter
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTableWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from GUI.tools import ImageLoader


class ImageTableWidget(QTableWidget):
    def __init__(self, parent: QWidget, save_path, logger, show_image_callback=None,
                 usethumbnail: bool = False, one_work: bool = False, update_info_callback=None):
        '''
        image_datas:
        '''
        super().__init__(parent)
        self.save_path = save_path
        self.update_info_callback = update_info_callback
        self.show_image_callback = show_image_callback
        self.logger = logger
        # 是否为单个作品
        self.one_work = one_work
        # 设置图片宽高
        self.default_img_width = 240  # 320
        self.default_img_height = 300  # 360
        self.img_width = 240
        self.img_height = 300
        # 设置行数和列数
        self.rows = 2
        self.columns = 4
        self.setRowCount(self.rows)
        self.setColumnCount(self.columns)
        # 设置大小
        # self.setBaseSize
        self.setFixedSize(
            self.default_img_width * self.columns + 10,
            self.default_img_height * self.rows + 10,
        )
        # 设置页码
        self.pagesize = self.rows * self.columns
        self.page = 1
        # 是否使用缩略图
        self.use_thumbnail = usethumbnail
        # 初始化UI界面
        self.initUI()
        # 开启线程池
        self.image_load_pool = QThreadPool()
        self.image_load_pool.setMaxThreadCount(4)

    def initUI(self):
        # 设置单元格宽高
        for i in range(self.rows):  # 让行高和图片相同
            self.setRowHeight(i, self.img_height)
        for i in range(self.columns):  # 让列宽和图片相同
            self.setColumnWidth(i, self.img_width)

        # 图片列表
        self.image_datas = []

        # 添加标签
        for i in range(self.rows):
            for j in range(self.columns):
                label = QLabel(self)
                # 设置对齐方式
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # QSS Qt StyleSheet
                label.setStyleSheet("QLabel{margin:5px};")
                # 设置与宽高
                label.setFixedSize(self.img_width, self.img_height)
                # 添加到tablewidget
                self.setCellWidget(i, j, label)

        # 禁止编辑
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # 设置单选
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        # 根据内容自动调整列合行
        # resizeColumnsToContents()
        # resizeRowsToContents()
        # 自定义表头和第一列，隐藏显示
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        # 隐藏表格线
        # self.setShowGrid(False)

        # 事件绑定
        if self.one_work:
            pass
        else:
            self.itemSelectionChanged.connect(self.update_image_info)
        self.doubleClicked.connect(self.show_original_image)

    # 已弃用
    def search(self, search_info):
        self.image_datas.clear()
        self.work_number = 0
        self.page = 1
        self.total_page = 1
        # self.results = None
        if re.findall(r"\+", search_info):
            and_search = []
            for one_search in search_info.split("+"):
                if re.search(r"\d{4,}", one_search):
                    and_search.append({"userId": one_search})
                else:
                    and_search.append(
                        {"tags." + one_search: {"$exists": "true"}})
            self.results = self.backup_collection.find(
                {"$and": and_search}).sort("id", -1)

        elif re.findall(r"\,", search_info):
            or_search = []
            for one_search in search_info.split(","):
                if re.search(r"\d{4,}", one_search):
                    or_search.append({"userId": one_search})
                else:
                    or_search.append(
                        {"tags." + one_search: {"$exists": "true"}})
                self.results = self.backup_collection.find(
                    {"$or": or_search}).sort("id", -1)

        elif search_info:
            one_search = {}
            if re.search(r"\d{4,}", search_info):
                one_search.update({"userId": search_info})
            else:
                one_search.update({"tags." + search_info: {"$exists": "true"}})
            self.results = self.backup_collection.find(
                one_search).sort("id", -1)

        else:
            self.results = self.backup_collection.find(
                {'id': {"$exists": "true"}}).sort("id", -1)

        for row in self.results:
            self.image_datas.append(row)
            self.work_number += 1

        self.total_page = (self.work_number -
                           1) // (self.rows * self.columns) + 1
        # print("总页数:%d"%(self.total_page))
        """
        #self.page_number = len(self.work_ids)//self.pagesize
        #if len(self.work_ids)%self.pagesize !=0:
        #    self.page_number+=1
        self.page_number = self.work_number//self.pagesize
        if self.work_number%self.pagesize !=0:
            self.page_number+=1
        print(self.page_number)
        """
        self.page = 1
        self.update_image_new()
        return self.page, self.total_page

    def update_image(self):
        self.images = self.image_datas[
            (self.page - 1) * self.pagesize: self.page * self.pagesize
        ]
        for i in range(self.rows):
            for j in range(self.columns):
                label = self.cellWidget(i, j)
                try:
                    relative_path = self.images[i * self.columns + j].get(
                        "relative_path"
                    )[0]
                except IndexError:
                    label.clear()
                    continue
                if self.use_thumbnail:
                    relative_path = re.search(
                        "(?<=picture/).*", relative_path).group()
                    path = self.save_path + "thumbnail/" + relative_path
                else:
                    path = self.save_path + relative_path
                pixmap = self.load_image(path)
                if pixmap == 2:
                    # print("加载图片失败:"+relative_path)
                    self.logger.warning("加载图片失败:" + relative_path)
                elif pixmap == 3:
                    label.setText("Not download")
                else:
                    label.setPixmap(pixmap)
                QApplication.processEvents()

    def load_image(self, path):
        """
        :return pixmap:缩放好的图片
        :return 2:加载图片失败
        :return 3:图片不存在
        """
        if os.path.exists(path):
            image = QImage(path)
            # image = QImage.fromData(data)
            # image = image.convertToFormat(QImage.Format.Format_ARGB32)
            image = image.scaled(
                self.img_width,
                self.img_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            pixmap = QPixmap()
            if pixmap.convertFromImage(image):
                return pixmap
            else:
                return 2
        else:
            return 3

    def update_image_new(self) -> None:
        self.image_load_pool.clear()
        if self.one_work:
            self.images = self.image_datas.get("relative_path")[
                (self.page - 1) * self.pagesize: self.page * self.pagesize
            ]
        else:
            self.images = self.image_datas[
                (self.page - 1) * self.pagesize: self.page * self.pagesize
            ]
        for i in range(self.rows):
            for j in range(self.columns):
                label = self.cellWidget(i, j)
                try:
                    if self.one_work:
                        relative_path = self.images[i * self.columns + j]
                    else:
                        relative_path = self.images[i * self.columns + j].get(
                            "relative_path"
                        )[0]
                except IndexError:
                    label.clear()
                    continue
                if self.use_thumbnail:
                    relative_path = re.search(
                        "(?<=picture/).*", relative_path).group()
                    path = self.save_path + "thumbnail/" + relative_path
                else:
                    path = self.save_path + relative_path
                index = (i, j)
                imageloader = ImageLoader(
                    self, self.img_width, self.img_height, index=index, image_path=path)
                self.image_load_pool.start(imageloader)

    @pyqtSlot(tuple, object)
    def set_image(self, index, args):
        """
        设置ImageLoader返回的图片(槽函数)
        :param index: 图片索引
        :param args: 图片加载代码以及加载的Qpixmap格式图片
        :return:
        """
        label = self.cellWidget(index[0], index[1])
        code = args[0]
        pixmap = args[1]
        if code == 2:
            self.logger.warning("加载图片失败!")
        elif code == 3:
            label.setText("Not download")
        elif code == 0:
            label.setPixmap(pixmap)
        # QApplication.processEvents()

    def update_image_info(self):
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            self.update_info_callback("", self.img_url, self.img_path)
            return
        index = index.row() * self.columns + index.column()
        try:
            result = self.images[index]
        except IndexError:
            self.update_info_callback("", "", "")
            return
        except AttributeError:
            self.update_info_callback("", "", "")
            return
        id = result.get("id")
        type = result.get("type")
        title = result.get("title")
        userid = result.get("userId")
        username = result.get("username")
        tags = result.get("tags")
        description = result.get("description")
        self.img_url = "https://www.pixiv.net/artworks/" + str(id)
        self.img_path = result.get("relative_path")[0]

        infos = "ID:{}\nType:{}\nTitle:{}\nUserID:{}\nUserName:{}\nTags:\n{}\nDescription:\n{}"
        self.update_info_callback(
            infos.format(id, type, title, userid, username, tags, description),
            self.img_url,
            self.img_path,
        )

    def show_original_image(self):
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            return
        index = index.row() * self.columns + index.column()
        try:
            result = self.images[index]
        except IndexError:
            return
        except AttributeError:
            return
        if self.one_work:
            id = self.image_datas.get("id")
            type = self.image_datas.get("type")
            title = self.image_datas.get("title")
            userid = self.image_datas.get("userId")
            username = self.image_datas.get("username")
            tags = self.image_datas.get("tags")
            description = self.image_datas.get("description")
            infos = "ID:{}\nType:{}\nTitle:{}\nUserID:{}\nUserName:{}\nTags:\n{}\nDescription:\n{}"
            infos = infos.format(id, type, title, userid,
                                 username, tags, description)
            result = (id, result, infos)
            self.show_image_callback(result)
        else:
            self.show_image_callback(result)

    def change_page(self, page):
        self.page = page
        # 清除选中
        # self.clearSelection()
        self.update_image_new()

    def resizeEvent(self, e) -> None:
        return super().resizeEvent(e)
        # 设置单元格宽高
        for i in range(self.rows):  # 让行高和图片相同
            self.setRowHeight(i, self.img_height)
        for i in range(self.columns):  # 让列宽和图片相同
            self.setColumnWidth(i, self.img_width)


class UserTableWidget(QTableWidget):
    def __init__(self, parent: QWidget, save_path, logger, db, show_image_callback=None,
                 usethumbnail: bool = False, update_info_callback=None):
        '''
        image_datas:
        '''
        super().__init__(parent)
        self.save_path = save_path
        self.update_info_callback = update_info_callback
        self.show_image_callback = show_image_callback
        self.db = db
        self.logger = logger
        # 设置图片宽高
        self.default_img_width = 200  # 320
        self.default_img_height = 160  # 360
        self.info_width = 240
        self.img_width = 200
        self.img_height = 160
        # 设置行数和列数
        self.rows = 4
        self.columns = 6
        self.setRowCount(self.rows)
        self.setColumnCount(self.columns)
        # 设置大小
        self.setFixedSize(
            self.info_width + self.default_img_width * self.columns + 10,
            self.default_img_height * self.rows + 10,
        )
        # 设置页码
        self.pagesize = 4  # 每页显示四个作者的信息
        self.page = 1
        # 是否使用缩略图
        self.use_thumbnail = usethumbnail
        # 初始化UI界面
        self.initUI()
        # 开启线程池
        self.image_load_pool = QThreadPool()
        self.image_load_pool.setMaxThreadCount(4)

    def initUI(self):
        # 设置单元格宽高
        for i in range(self.rows):  # 让行高和图片相同
            self.setRowHeight(i, self.img_height)
        self.setColumnWidth(0, self.info_width)
        for i in range(1, self.columns):  # 让列宽和图片相同
            self.setColumnWidth(i, self.img_width)

        # 作者列表
        self.user_datas = []

        # 添加标签
        for i in range(self.rows):
            for j in range(self.columns):
                if j == 0:
                    textbrowser = QTextBrowser(self)
                    textbrowser.setFixedSize(self.info_width, self.img_height)
                    self.setCellWidget(i, j, textbrowser)
                else:
                    label = QLabel(self)
                    # 设置对齐方式
                    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    # QSS Qt StyleSheet
                    label.setStyleSheet("QLabel{margin:5px};")
                    # 设置与宽高
                    label.setFixedSize(self.img_width, self.img_height)
                    # 添加到tablewidget
                    self.setCellWidget(i, j, label)

        # 禁止编辑
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # 设置单行选择
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        # 自定义表头和第一列，隐藏显示
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(False)
        # 隐藏表格线
        # self.setShowGrid(False)

        # 事件绑定
        self.doubleClicked.connect(self.show_original_image)

    # 已弃用
    def search(self, search_info):
        self.image_datas.clear()
        self.work_number = 0
        self.page = 1
        self.total_page = 1
        # self.results = None
        if re.findall(r"\+", search_info):
            and_search = []
            for one_search in search_info.split("+"):
                if re.search(r"\d{4,}", one_search):
                    and_search.append({"userId": one_search})
                else:
                    and_search.append(
                        {"tags." + one_search: {"$exists": "true"}})
            self.results = self.backup_collection.find(
                {"$and": and_search}).sort("id", -1)

        elif re.findall(r"\,", search_info):
            or_search = []
            for one_search in search_info.split(","):
                if re.search(r"\d{4,}", one_search):
                    or_search.append({"userId": one_search})
                else:
                    or_search.append(
                        {"tags." + one_search: {"$exists": "true"}})
                self.results = self.backup_collection.find(
                    {"$or": or_search}).sort("id", -1)

        elif search_info:
            one_search = {}
            if re.search(r"\d{4,}", search_info):
                one_search.update({"userId": search_info})
            else:
                one_search.update({"tags." + search_info: {"$exists": "true"}})
            self.results = self.backup_collection.find(
                one_search).sort("id", -1)

        else:
            self.results = self.backup_collection.find(
                {'id': {"$exists": "true"}}).sort("id", -1)

        for row in self.results:
            self.image_datas.append(row)
            self.work_number += 1

        self.total_page = (self.work_number -
                           1) // (self.rows * self.columns) + 1
        # print("总页数:%d"%(self.total_page))
        """
        #self.page_number = len(self.work_ids)//self.pagesize
        #if len(self.work_ids)%self.pagesize !=0:
        #    self.page_number+=1
        self.page_number = self.work_number//self.pagesize
        if self.work_number%self.pagesize !=0:
            self.page_number+=1
        print(self.page_number)
        """
        self.page = 1
        self.update_image_new()
        return self.page, self.total_page

    def update_user_info(self) -> None:
        self.image_load_pool.clear()
        self.users = self.user_datas[
            (self.page - 1) * self.pagesize: self.page * self.pagesize
        ]
        for i in range(self.rows):
            textbrowser = self.cellWidget(i, 0)
            try:
                user_info = self.users[i]
            except IndexError:
                textbrowser.clear()
                for j in range(1, self.columns):
                    self.cellWidget(i, j).clear()
                continue
            info = "userName:{}\nuserId:{}\nuserComment:{}".format(
                user_info["userName"], user_info["userId"], user_info.get(
                    "userComment")
            )
            textbrowser.setPlainText(info)
            collection = self.db[user_info["userName"]]
            images = collection.find({"id": {"$exists": "true"}}, {
                                     "_id": 0, "relative_path": 1}).sort("id", -1).limit(self.columns)
            for j in range(1, self.columns):
                label = self.cellWidget(i, j)
                try:
                    relative_path = images[j - 1].get("relative_path")[0]
                except IndexError:
                    label.clear()
                    continue
                if self.use_thumbnail:
                    relative_path = re.search(
                        "(?<=picture/).*", relative_path).group()
                    path = self.save_path + "thumbnail/" + relative_path
                else:
                    path = self.save_path + relative_path
                index = (i, j)
                imageloader = ImageLoader(
                    self, self.img_width, self.img_height, index=index, image_path=path)
                self.image_load_pool.start(imageloader)

    @pyqtSlot(tuple, object)
    def set_image(self, index, args):
        """
        设置ImageLoader返回的图片(槽函数)
        :param index: 图片索引
        :param args: 图片加载代码以及加载的Qpixmap格式图片
        :return:
        """
        label = self.cellWidget(index[0], index[1])
        code = args[0]
        pixmap = args[1]
        if code == 2:
            self.logger.warning("加载图片失败!")
        elif code == 3:
            label.setText("Not download")
        elif code == 0:
            label.setPixmap(pixmap)
        # QApplication.processEvents()

    def show_original_image(self):
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            return
        row = index.row()
        try:
            result = self.users[row]
        except IndexError:
            return
        except AttributeError:
            return
        print(result)
        # self.show_image_callback(result)

    def change_page(self, page):
        self.page = page
        # 清除选中
        # self.clearSelection()
        self.update_user_info()

    def resizeEvent(self, e) -> None:
        self.setFixedSize(
            self.info_width + self.default_img_width * self.columns + 10,
            self.default_img_height * self.rows + 10,
        )
        return super().resizeEvent(e)
        # 设置单元格宽高
        for i in range(self.rows):  # 让行高和图片相同
            self.setRowHeight(i, self.img_height)
        for i in range(self.columns):  # 让列宽和图片相同
            self.setColumnWidth(i, self.img_width)


class ExtendedComboBox(QComboBox):
    """
    扩展ComboBox插件 增加Items模糊搜索功能
    """

    def __init__(self, parent):
        super(ExtendedComboBox, self).__init__(parent)
        self.setEditable(True)

        # add a filter model to filter matching items
        self.pFilterModel = QSortFilterProxyModel(self)
        self.pFilterModel.setFilterCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive)
        self.pFilterModel.setSourceModel(self.model())

        # add a completer, which uses the filter model
        self.completer = QCompleter(self.pFilterModel, self)
        # always show all (filtered) completions
        self.completer.setCompletionMode(
            QCompleter.CompletionMode.UnfilteredPopupCompletion
        )
        self.setCompleter(self.completer)

        # connect signals
        # self.lineEdit().textEdited.connect(self.pFilterModel.setFilterFixedString)
        self.completer.activated.connect(self.on_completer_activated)

    # on selection of an item from the completer, select the corresponding item from combobox
    def on_completer_activated(self, text):
        if text:
            # index = self.findText(text)
            # self.setCurrentIndex(index)
            # self.activated[str].emit(self.itemText(index))
            pass

    # on model change, update the models of the filter and completer as well
    def setModel(self, model):
        super(ExtendedComboBox, self).setModel(model)
        self.pFilterModel.setSourceModel(model)
        self.completer().setModel(self.pFilterModel)

    # on model column change, update the model column of the filter and completer as well
    def setModelColumn(self, column):
        self.completer().setCompletionColumn(column)
        self.pFilterModel.setFilterKeyColumn(column)
        super(ExtendedComboBox, self).setModelColumn(column)


class ScrollArea(QScrollArea):
    def __init__(self, parent: QWidget, logger, db, savepath: str, usethumbnail: bool = False):
        super().__init__(parent)
        self.save_path = savepath
        self.logger = logger
        self.db = db
        self.use_thumbnail = usethumbnail
        self.all_users = []
        allfollowing = db["All Followings"]
        for one in allfollowing.find(
            {"userId": {"$exists": "true"}}, {"_id": 0}
        ):
            self.all_users.append(one)
        self.page = 1
        self.pagesize = 8
        self.total_page = (
            allfollowing.count_documents(
                {"userId": {"$exists": "true"}})
            // self.pagesize
            + 1
        )
        # 开启线程池
        self.image_load_pool = QThreadPool()
        self.image_load_pool.setMaxThreadCount(8)
        self.initUI()
        self.show_user_info()

    def initUI(self):
        self.widget0 = QWidget()  # Widget that contains the collection of Vertical Box
        self.vbox = (
            QVBoxLayout()
        )  # The Vertical Box that contains the Horizontal Boxes of  labels and buttons

        self.img_width = 240
        self.img_height = 300

        self.widget0.setLayout(self.vbox)

        # Scroll Area Properties
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.widget0)
        self.verticalScrollBar().valueChanged.connect(self.stream_load)

    @pyqtSlot(QLabel, object)
    def set_image(self, label, args):
        """
        设置ImageLoader返回的图片(槽函数)
        :param label: 标签对象
        :param args: 图片加载代码以及加载的Qpixmap格式图片
        :return:
        """
        code = args[0]
        pixmap = args[1]
        if code == 2:
            self.logger.warning("加载图片失败!")
        elif code == 3:
            label.setText("Not download")
        elif code == 0:
            label.setPixmap(pixmap)
        # QApplication.processEvents()

    def load_image(self, path):
        """
        :return pixmap:缩放好的图片
        :return 2:加载图片失败
        :return 3:图片不存在
        """
        if os.path.exists(path):
            image = QImage(path)
            # image = QImage.fromData(data)
            # image = image.convertToFormat(QImage.Format.Format_ARGB32)
            image = image.scaled(
                self.img_width,
                self.img_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            pixmap = QPixmap()
            if pixmap.convertFromImage(image):
                return pixmap
            else:
                return 2
        else:
            return 3

    def stream_load(self):
        if self.verticalScrollBar().value() == self.verticalScrollBar().maximum():
            if self.page < self.total_page:
                self.page += 1
                # print('Loading...')
                # logger.info("Loading...")
                self.show_user_info()

    def show_user_info(self):
        self.image1s = []
        if len(self.all_users) >= 8:
            user_infos = self.all_users[
                (self.page - 1) * self.pagesize: self.page * self.pagesize
            ]
        else:
            user_infos = self.all_users
        for user_info in user_infos:
            layout = QHBoxLayout()
            info = "userName:{}\nuserId:{}\nuserComment:{}".format(
                user_info["userName"], user_info["userId"], user_info.get(
                    "userComment")
            )
            userinfoDisplear = QTextBrowser()
            userinfoDisplear.setFixedSize(self.img_width, self.img_height)
            userinfoDisplear.setPlainText(info)
            layout.addWidget(userinfoDisplear)
            collection = self.db[user_info["userName"]]
            for one in (
                collection.find(
                    {"id": {"$exists": "true"}}, {"_id": 0, "relative_path": 1}
                )
                .sort("id", -1)
                .limit(4)
            ):
                relative_path = one.get("relative_path")[0]
                if self.use_thumbnail:
                    relative_path = re.search(
                        "(?<=picture/).*", relative_path).group()
                    path = self.save_path + \
                        "thumbnail/" + relative_path
                else:
                    path = self.save_path + relative_path
                label = QLabel()
                # 设置对齐方式
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # QSS Qt StyleSheet
                label.setStyleSheet("QLabel{margin:1px};")
                # 设置与宽高
                label.setFixedSize(self.img_width, self.img_height)
                pixmap = self.load_image(path)
                if pixmap == 2:
                    # print("加载图片失败:"+relative_path)
                    self.logger.warning("加载图片失败:" + relative_path)
                elif pixmap == 3:
                    label.setText("Not download")
                else:
                    # 显示图片
                    label.setPixmap(pixmap)
                layout.addWidget(label)
            self.vbox.addLayout(layout)

    def show_user_info_new(self):
        self.image1s = []
        if len(self.all_users) >= 8:
            user_infos = self.all_users[
                (self.page - 1) * self.pagesize: self.page * self.pagesize
            ]
        else:
            user_infos = self.all_users
        for user_info in user_infos:
            layout = QHBoxLayout()
            info = "userName:{}\nuserId:{}\nuserComment:{}".format(
                user_info["userName"], user_info["userId"], user_info.get(
                    "userComment")
            )
            userinfoDisplear = QTextBrowser()
            userinfoDisplear.setFixedSize(self.img_width, self.img_height)
            userinfoDisplear.setPlainText(info)
            layout.addWidget(userinfoDisplear)
            collection = self.db[user_info["userName"]]
            for one in (
                collection.find(
                    {"id": {"$exists": "true"}}, {"_id": 0, "relative_path": 1}
                )
                .sort("id", -1)
                .limit(4)
            ):
                relative_path = one.get("relative_path")[0]
                if self.use_thumbnail:
                    relative_path = re.search(
                        "(?<=picture/).*", relative_path).group()
                    path = self.save_path + \
                        "thumbnail/" + relative_path
                else:
                    path = self.save_path + relative_path
                label = QLabel()
                # 设置对齐方式
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # QSS Qt StyleSheet
                label.setStyleSheet("QLabel{margin:1px};")
                # 设置与宽高
                label.setFixedSize(self.img_width, self.img_height)
                imageloader = ImageLoader(
                    self, self.img_width, self.img_height, target=label, image_path=path)
                self.image_load_pool.start(imageloader)
                layout.addWidget(label)
            self.vbox.addLayout(layout)


class ImageBox(QWidget):
    def __init__(self):
        super(ImageBox, self).__init__()
        self.img = None
        self.scaled_img = None
        self.point = QPoint(0, 0)
        self.start_pos = None
        self.end_pos = None
        self.left_click = False
        self.scale = 1

    def set_image(self, img_path):
        """
        open image file
        :param img_path: image file path
        :return:
        """
        # img = QImageReader(img_path)
        # img.setScaledSize(QSize(self.size().width(), self.size().height()))
        # img = img.read()
        self.img = QPixmap(img_path)
        self.scaled_img = self.img

    def paintEvent(self, e):
        """
        receive paint events
        :param e: QPaintEvent
        :return:
        """
        if self.scaled_img:
            painter = QPainter()
            painter.begin(self)
            painter.scale(self.scale, self.scale)
            painter.drawPixmap(self.point, self.scaled_img)
            painter.end()

    def wheelEvent(self, event):
        angle = event.angleDelta() / 8  # 返回QPoint对象，为滚轮转过的数值，单位为1/8度
        angleY = angle.y()
        # 获取当前鼠标相对于view的位置
        if angleY > 0:
            self.scale *= 1.1
        else:  # 滚轮下滚
            self.scale *= 0.9
        self.adjustSize()
        self.update()

    def mouseMoveEvent(self, e):
        """
        mouse move events for the widget
        :param e: QMouseEvent
        :return:
        """
        if self.left_click:
            self.end_pos = e.pos() - self.start_pos
            self.point = self.point + self.end_pos*(1/self.scale)
            self.start_pos = e.pos()
            self.repaint()

    def mousePressEvent(self, e):
        """
        mouse press events for the widget
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.MouseButton.LeftButton:
            self.left_click = True
            self.start_pos = e.pos()

    def mouseReleaseEvent(self, e):
        """
        mouse release events for the widget
        :param e: QMouseEvent
        :return:
        """
        if e.button() == Qt.MouseButton.LeftButton:
            self.left_click = False
