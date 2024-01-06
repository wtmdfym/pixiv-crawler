# -*-coding:utf-8-*-
import logging
import os
import sys
import pymongo
import motor.motor_asyncio
from PyQt6.QtCore import (
    QCoreApplication,
    QMetaObject,
    QRect,
    Qt,
)
from PyQt6.QtGui import QImageReader, QFont     # , QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QMenuBar,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    # QTabBar,
    QWidget,
    # QSystemTrayIcon,
)

import pixiv_pyqt_tools
# from GUI.widgets import
# , ImageTab, OriginalImageTab
from GUI.tabs import MainTab, SearchTab, TagsTab, UserTab, ConfigTab

# 日志信息
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(
#     format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S",
#     level=logging.DEBUG)
# logger = logging.getLogger('basic_logger')
# logger.propagate = False
formatter = logging.Formatter("%(asctime)s : [%(levelname)s] - %(message)s")
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)

# =================================================
#                    默认信息
# =================================================
# 登录状态验证信息
# cookie = ''
# oringal_cookie = 'first_visit_datetime_pc=2023-01-23+00%3A14%3A42; p_ab_id=3; p_ab_id_2=5; p_ab_d_id=969409743;\
#  yuid_b=EohWKGY; _gcl_au=1.1.1590819832.1674400503; __utmz=235335808.1674400504.1.1.utmcsr=(direct)|utmccn=(dir\
# ect)|utmcmd=(none); PHPSESSID=83945559_gjvPa6Zamm7D9DlhBlOUVzmXDtibWk0h; device_token=a9d02fd82ed56073ee9c405ea\
# 9c43b68; privacy_policy_agreement=5; _ga_MZ1NL4PHH0=GS1.1.1674400510.1.1.1674400548.0.0.0; c_type=23; privacy_p\
# olicy_notification=0; a_type=0; b_type=1; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; login_ever=yes; __utmv=235335808.|2=l\
# ogin%20ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=83945559=1^9=p_ab_id=3=1^10=p_ab_id_2=5=1^11=lang=z\
# h=1; _ga=GA1.1.1220638934.1674400503; __utma=235335808.1220638934.1674400503.1674973853.1674976751.22; __utmc=2\
# 35335808; __utmt=1; tag_view_ranking=0xsDLqCEW6~qWFESUmfEs~_EOd7bsGyl~Lt-oEicbBr~aKhT3n4RHZ~TqiZfKmSCg~OgLi_QXW\
# K2~gnmsbf1SSR~0jyux9PxkH~SZJe4DVQ3-~LX3_ayvQX4~4TDL3X7bV9~m3EJRa33xU~zIv0cf5VVk~HLTvFcV98c~S0eWMRWoH6~q3eUobDMJ\
# W~RTJMXD26Ak~l5mRf3lmn2~BtXd1-LPRH~75zhzbk0bS~TV3I2h_Vd8~tlXeaI4KBb~gzY20gtW1F~WI561SX4pn~jH0uD88V6F~LVSDGaCAdn\
# ~ziiAzr_h04~9vxLUp1ZIl~qXzcci65nj~aMSPvw-ONW~OYl5wlor4w~MnGbHeuS94~u8McsBs7WV~Ie2c51_4Sp~39hg5DAst3~ckiinMU_tG~\
# Z-FJ6AMFu8~xha5FQn_XC~Je_lQPk0GY~jhuUT0OJva~PwDMGzD6xn~GCo59yAyB6~SqVgDNdq49~BMGWRnllLS~-vjApZay9I~X8lyQqDJ_c~r\
# pKQpa_qll~R4-PiPeYtW~XyYiM1QdJg~AajMyHII2s~vACH6E5K7c~rIC2oNFqzh~LLyDB5xskQ~IRbM9pb4Zw~U-RInt8VSZ~ef1QMXOaBg~AV\
# ueVDbpwj~eVxus64GZU~4QveACRzn3~nK5hU21ePB~DuZWAJi-O1~uW5495Nhg-~MM6RXH_rlN~xjfPXTyrpQ~hrDZxHZLs1~uC2yUZfXDc~LtW\
# -gO6CmS~gCB7z_XWkp~1TeQXqAyHD~GNcgbuT3T-~uRvwDns1lH~b_rY80S-DW~eInvgwdvwj~k3AcsamkCa~erWmq3nmlB~oDcj90OVdf~ti_E\
# 1boC1J~NGpDowiVmM~faHcYIP1U0~xVHdz2j0kF~7dpqkQl8TH~f5JQP46dEd~TWrozby2UO~HK5v86l5Tm~CZnOKinv48~SWfYs94Rgz~2kSJB\
# y_FeR~0xRZYD1xTs~liM64qjhwQ~hk4MlvHBiP~W-PCidtmJv~-ErGQUWHGl~cmn1GxZ53u~QM0rfezNVP~XwbsX1-yIW~GX5cZxE2GY~b_G3UD\
# fpN0~bQ1-GzNhfP~ETjPkL0e6r; _ga_75BBYNYN9J=GS1.1.1674976753.21.1.1674976780.0.0.0; __utmb=235335808.4.10.167497\
# 6751'


class MyLogging(logging.Logger):
    def __init__(self) -> None:
        super().__init__(self)

    def init(self, usestream, infodisplayer):
        if usestream:
            self.usestream = True
        else:
            self.usestream = False
            self.infodisplayer = infodisplayer

    def debug(self,
              msg: object,
              *args: object,
              exc_info=None,
              stack_info: bool = False,
              stacklevel: int = 1,
              extra=None) -> None:
        if self.usestream:
            return super().debug(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra)

    def info(
        self,
        msg: object,
        *args: object,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra=None,
    ) -> None:
        if self.usestream:
            return super().info(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )
        else:
            self.infodisplayer.append("[INFO] - %s" % msg)

    def warning(
        self,
        msg: object,
        *args: object,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra=None,
    ) -> None:
        if self.usestream:
            return super().warning(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )
        else:
            self.infodisplayer.append("[WARNING] - %s" % msg)

    def error(
        self,
        msg: object,
        *args: object,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra=None,
    ) -> None:
        if self.usestream:
            return super().error(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )
        else:
            self.infodisplayer.append("[ERROR] - %s" % msg)

    def critical(
        self,
        msg: object,
        *args: object,
        exc_info=None,
        stack_info: bool = False,
        stacklevel: int = 1,
        extra=None,
    ) -> None:
        if self.usestream:
            return super().critical(
                msg,
                *args,
                exc_info=exc_info,
                stack_info=stack_info,
                stacklevel=stacklevel,
                extra=extra,
            )
        else:
            self.infodisplayer.append("[CRITICAL] - %s" % msg)


'''
class Ui_MainWindow(object):
    def setupUi(self,  MainWindow):
        self.MainWindow = MainWindow
        self.config_save_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "config.json"
        )
        self.config_dict = pixiv_pyqt_tools.ConfigSetter.get_config(
            self.config_save_path)
        # 初始化数据库
        # global db, backup_collection
        # global asyncdb, asyncbackup_collection
        client = pymongo.MongoClient("localhost", 27017)
        asyncclient = motor.motor_asyncio.AsyncIOMotorClient(
            'localhost', 27017)
        self.db = client["pixiv"]
        self.asyncdb = asyncclient["pixiv"]
        self.backup_collection = client["backup"]["backup of pixiv infos"]
        self.asyncbackup_collection = asyncclient["backup"]["backup of pixiv infos"]
        self.default_width = 1260
        self.default_height = 768
        # 设置最小大小
        # self.width_ratio = 1
        # self.height_ratio = 1
        self.default_tab_width = 1240
        self.default_tab_height = 732
        # 设置图片最大大小
        QImageReader.setAllocationLimit(256)
        # Tab数量
        self.tab_count = 5

        # 初始化tabWidget
        self.centralwidget = QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QTabWidget(parent=self.centralwidget)
        self.tabWidget.setGeometry(
            QRect(0, 0, self.default_tab_width, self.default_tab_height)
        )
        self.tabWidget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.North)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget.setDocumentMode(False)
        self.tabWidget.setObjectName("tabWidget")
        # 设置tab可关闭
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)
        # self.tabWidget.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)
        # 初始化MainTab
        self.tab = MainTab(MainWindow, self.config_dict, self.config_save_path, self.db,
                           self.backup_collection, self.asyncdb, self.asyncbackup_collection, logger)
        self.tab.setObjectName("MainTab")
        self.tabWidget.addTab(self.tab, "")
        # 初始化SearchTab
        self.tab_1 = SearchTab(
            MainWindow, self.config_dict["save_path"], logger, self.backup_collection,
            self.creat_image_tab, self.config_dict["use_thumbnail"])
        self.tab_1.setObjectName("SearchTab")
        self.tabWidget.addTab(self.tab_1, "")
        # 初始化TagsTab
        self.tab_2 = TagsTab(
            MainWindow,
            self.db,
            changetab=self.tabWidget.setCurrentIndex,
            settext=self.tab_1.searchEdit.setText,
        )
        self.tab_2.setObjectName("TagsTab")
        self.tabWidget.addTab(self.tab_2, "")
        # 初始化UserTab
        self.tab_3 = UserTab(
            MainWindow, logger, self.db, self.config_dict["save_path"], self.config_dict["use_thumbnail"])
        self.tab_3.setObjectName("UserTab")
        self.tabWidget.addTab(self.tab_3, "")
        # 初始化ConfigsTab
        self.tab_4 = ConfigTab(MainWindow, logger, self.config_dict,
                               self.config_save_path, self.db, self.reloadUI)
        self.tab_4.setObjectName("ConfigsTab")
        self.tabWidget.addTab(self.tab_4, "")
        # 设置主窗口
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QRect(0, 0, 768, 22))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QMenu(parent=self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(1)
        # self.statusbar.showMessage
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        # 显示翻译
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tab.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab), _translate(
                "MainWindow", "Main")
        )
        self.tab_1.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_1), _translate(
                "MainWindow", "Search")
        )
        self.tab_2.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2), _translate(
                "MainWindow", "Tags")
        )
        # self.tab_3.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_3), _translate(
                "MainWindow", "User")
        )
        self.tab_4.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_4), _translate(
                "MainWindow", "Settings")
        )
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))

    def resizeEvent(self, a0) -> None:
        new_width = self.MainWindow.width()
        new_height = self.MainWindow.height()
        width_ratio = new_width / self.default_width
        height_ratio = new_height / self.default_height
        # if self.width_ratio != width_ratio or self.height_ratio != height_ratio:
        #    self.width_ratio = width_ratio
        #    self.height_ratio = height_ratio
        # self.tab.resize(int(self.tab.default_width*width_ratio), int(self.tab.default_height*height_ratio))
        self.tabWidget.resize(
            int(self.default_tab_width * width_ratio),
            int(self.default_tab_height * height_ratio),
        )
        self.tab.resize(
            int(self.tab.default_width * width_ratio),
            int(self.tab.default_height * height_ratio),
        )
        self.tab_1.resize(
            int(self.tab_1.default_width * width_ratio),
            int(self.tab_1.default_height * height_ratio),
        )
        self.tab_2.resize(
            int(self.tab_2.default_width * width_ratio),
            int(self.tab_2.default_height * height_ratio),
        )
        self.tab_3.resize(
            int(self.tab_3.default_width * width_ratio),
            int(self.tab_3.default_height * height_ratio),
        )
        self.tab_4.resize(
            int(self.tab_4.default_width * width_ratio),
            int(self.tab_4.default_height * height_ratio),
        )
        return self.MainWindow.resizeEvent(a0)

    def reloadUI(self):
        # 重新加载设置
        global config_dict, logger
        config_dict = pixiv_pyqt_tools.ConfigSetter.get_config(
            self.config_save_path)
        """
        # 弹出提示框
        info_box = QMessageBox()
        info_box.setWindowTitle("Pixiv")     # QMessageBox标题
        info_box.setText("重新加载窗口")      # QMessageBox的提示文字
        info_box.setStandardButtons(
            QMessageBox.StandardButton.Ok)      # QMessageBox显示的按钮

        info_box.button(QMessageBox.StandardButton.Ok).animateClick()
        info_box.exec()    # 如果使用.show(),会导致QMessageBox框一闪而逝
        time.sleep(1)
        # self.timer = QTimer(self)  # 初始化一个定时器
        """
        # 重新加载窗口
        self.MainWindow.destroy(True, True)
        self.setupUi(self.MainWindow)
        # 重新设置logger
        logger = MyLogging()
        logger.init(
            ui.config_dict["enable_console_output"], ui.tab.infodisplayer)
        logger.addHandler(console_handler)

    def creat_image_tab(self, image_data: dict | tuple):
        # print(image_data)
        if isinstance(image_data, dict):
            id = image_data.get("id")
            if len(image_data.get("relative_path")) == 1:
                tab = OriginalImageTab(image_data)
                tab.open_image(
                    self.config_dict["save_path"]+image_data.get("relative_path")[0])
            else:
                tab = ImageTab(self.MainWindow, self.config_dict["save_path"], logger, image_data,
                               self.creat_image_tab, self.config_dict["use_thumbnail"])
            index = self.tabWidget.insertTab(2, tab, str(id))
        else:
            id = image_data[0]
            img_path = image_data[1]
            tab = OriginalImageTab()   # image_data[2]
            tab.open_image(self.config_dict["save_path"]+img_path)
            index = self.tabWidget.insertTab(self.tab_count - 3, tab, str(id))
        self.tabWidget.setCurrentIndex(index)
        self.tab_count += 1
        # self.tabWidget.addTab(tab, str(id))

    def close_tab(self, index):
        if index <= 1 or index >= (self.tab_count - 3):
            return
        self.tabWidget.removeTab(index)
        self.tabWidget.setCurrentIndex(index - 1)
        self.tab_count -= 1


class mainwindow(QMainWindow):
    def __init__(self, scaleRate):
        super().__init__()
        # 大概是继承了 Ui_MainWindow 的缘故，这里直接使用 setupUI()
        # 初始化设置信息
        self.setObjectName("MainWindow")
        # PyQt6获取屏幕参数
        screen = QApplication.primaryScreen().size()
        self.default_width = 1260
        self.default_height = 768
        # 设置最小大小
        self.setMinimumSize(self.default_width, self.default_height)
        # self.width_ratio = 1
        # self.height_ratio = 1
        self.default_tab_width = 1240
        self.default_tab_height = 732
        # 居中显示
        width = int(self.default_width * scaleRate)
        height = int(self.default_height * scaleRate)
        self.setGeometry(
            QRect(
                (screen.width() - width) // 2,
                (screen.height() - height) // 2,
                width,
                height,
            )
        )

        self.setWindowTitle("Pixiv Crawler")
        # 设置图片最大大小
        QImageReader.setAllocationLimit(256)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, MainWindow, parent=None):
        super(TrayIcon, self).__init__(parent)
        self.ui = MainWindow
        self.createMenu()

    def createMenu(self):
        self.menu = QMenu()
        self.showAction1 = QAction("启动", self, triggered=self.show_window)
        self.quitAction = QAction("退出", self, triggered=self.quit)

        self.menu.addAction(self.showAction1)
        self.menu.addAction(self.quitAction)
        self.setContextMenu(self.menu)

        # 设置图标
        self.setIcon(QIcon(
            "pixiv-crawler/gui.py"))

        # 把鼠标点击图标的信号和槽连接
        self.activated.connect(self.onIconClicked)

    def show_window(self):
        # 若是最小化，则先正常显示窗口，再变为活动窗口（暂时显示在最前面）
        self.ui.showNormal()
        self.ui.activateWindow()

    def quit(self):
        pass
        # qApp.quit()

    # 鼠标点击icon传递的信号会带有一个整形的值，1是表示单击右键，2是双击，3是单击左键，4是用鼠标中键点击
    def onIconClicked(self, reason):
        if reason == 2 or reason == 3:
            # self.showMessage("Message", "skr at here", self.icon)
            if self.ui.isMinimized() or not self.ui.isVisible():
                # 若是最小化，则先正常显示窗口，再变为活动窗口（暂时显示在最前面）
                self.ui.showNormal()
                self.ui.activateWindow()

                self.ui.show()
            else:
                # 若不是最小化，则最小化
                self.ui.showMinimized()

                self.ui.show()
'''


class MainWindow(QMainWindow):
    def __init__(self, scaleRate):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Pixiv Crawler")
        # 初始化设置信息
        self.config_save_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "config.json"
        )
        self.config_dict = pixiv_pyqt_tools.ConfigSetter.get_config(
            self.config_save_path)
        # 初始化协程事件循环
        # self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(self.loop)
        # 初始化数据库
        # global db, backup_collection
        # global asyncdb, asyncbackup_collection
        client = pymongo.MongoClient("localhost", 27017)
        asyncclient = motor.motor_asyncio.AsyncIOMotorClient(
            'localhost', 27017)     # , io_loop=self.loop
        self.db = client["pixiv"]
        self.asyncdb = asyncclient["pixiv"]
        self.backup_collection = client["backup"]["backup of pixiv infos"]
        self.asyncbackup_collection = asyncclient["backup"]["backup of pixiv infos"]
        # PyQt6获取屏幕参数
        screen = QApplication.primaryScreen().size()
        self.default_width = 1260
        self.default_height = 768
        # 设置最小大小
        self.setMinimumSize(self.default_width, self.default_height)
        # self.width_ratio = 1
        # self.height_ratio = 1
        self.default_tab_width = 1240
        self.default_tab_height = 732
        # 居中显示
        width = int(self.default_width * scaleRate)
        height = int(self.default_height * scaleRate)
        self.setGeometry(
            QRect(
                (screen.width() - width) // 2,
                (screen.height() - height) // 2,
                width,
                height,
            )
        )
        # 设置图片最大大小
        QImageReader.setAllocationLimit(256)
        self.setupUi()

    def setupUi(self):
        # Tab数量
        self.tab_count = 5
        # 初始化tabWidget
        self.centralwidget = QWidget(parent=self)
        self.centralwidget.setObjectName("centralwidget")
        self.tabWidget = QTabWidget(parent=self.centralwidget)
        self.tabWidget.setGeometry(
            QRect(0, 0, self.default_tab_width, self.default_tab_height)
        )
        self.tabWidget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
        )
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.North)
        self.tabWidget.setTabShape(QTabWidget.TabShape.Rounded)
        self.tabWidget.setDocumentMode(False)
        self.tabWidget.setObjectName("tabWidget")
        # 设置tab可关闭
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.close_tab)
        # self.tabWidget.tabBar().setTabButton(0, QTabBar.ButtonPosition.RightSide, None)
        # 初始化MainTab
        self.tab = MainTab(self, self.config_dict, self.config_save_path, self.db,  # , self.loop
                           self.backup_collection, self.asyncdb, self.asyncbackup_collection, logger)
        self.tab.setObjectName("MainTab")
        self.tabWidget.addTab(self.tab, "")
        # 初始化SearchTab
        self.tab_1 = SearchTab(
            self, self.config_dict["save_path"], logger, self.backup_collection,
            self.creat_image_tab, self.config_dict["use_thumbnail"])
        self.tab_1.setObjectName("SearchTab")
        self.tabWidget.addTab(self.tab_1, "")
        # 初始化TagsTab
        self.tab_2 = TagsTab(
            self,
            self.db,
            changetab=self.tabWidget.setCurrentIndex,
            settext=self.tab_1.searchEdit.setText,
        )
        self.tab_2.setObjectName("TagsTab")
        self.tabWidget.addTab(self.tab_2, "")
        # 初始化UserTab
        self.tab_3 = UserTab(
            self, logger, self.db, self.config_dict["save_path"], self.config_dict["use_thumbnail"])
        self.tab_3.setObjectName("UserTab")
        self.tabWidget.addTab(self.tab_3, "")
        # 初始化ConfigsTab
        self.tab_4 = ConfigTab(self, logger, self.config_dict,
                               self.config_save_path, self.db, self.reloadUI)
        self.tab_4.setObjectName("ConfigsTab")
        self.tabWidget.addTab(self.tab_4, "")
        # 设置主窗口
        self.setCentralWidget(self.centralwidget)
        # 设置菜单栏
        self.menubar = QMenuBar(parent=self)
        self.menubar.setGeometry(QRect(0, 0, 768, 22))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QMenu(parent=self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.setMenuBar(self.menubar)
        # 设置状态栏
        self.statusbar = QStatusBar(parent=self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuHelp.menuAction())
        # 显示文字
        self.retranslateUi()
        self.tabWidget.setCurrentIndex(1)
        # self.statusbar.showMessage
        QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        # 显示翻译
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.tab.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab), _translate(
                "MainWindow", "Main")
        )
        self.tab_1.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_1), _translate(
                "MainWindow", "Search")
        )
        self.tab_2.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_2), _translate(
                "MainWindow", "Tags")
        )
        self.tab_3.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_3), _translate(
                "MainWindow", "User")
        )
        self.tab_4.retranslateUi()
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_4), _translate(
                "MainWindow", "Settings")
        )
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))

    def resizeEvent(self, a0) -> None:
        new_width = self.width()
        new_height = self.height()
        width_ratio = new_width / self.default_width
        height_ratio = new_height / self.default_height
        # if self.width_ratio != width_ratio or self.height_ratio != height_ratio:
        #    self.width_ratio = width_ratio
        #    self.height_ratio = height_ratio
        # self.tab.resize(int(self.tab.default_width*width_ratio), int(self.tab.default_height*height_ratio))
        self.tabWidget.resize(
            int(self.default_tab_width * width_ratio),
            int(self.default_tab_height * height_ratio),
        )
        self.tab.resize(
            int(self.tab.default_width * width_ratio),
            int(self.tab.default_height * height_ratio),
        )
        self.tab_1.resize(
            int(self.tab_1.default_width * width_ratio),
            int(self.tab_1.default_height * height_ratio),
        )
        self.tab_2.resize(
            int(self.tab_2.default_width * width_ratio),
            int(self.tab_2.default_height * height_ratio),
        )
        self.tab_3.resize(
            int(self.tab_3.default_width * width_ratio),
            int(self.tab_3.default_height * height_ratio),
        )
        self.tab_4.resize(
            int(self.tab_4.default_width * width_ratio),
            int(self.tab_4.default_height * height_ratio),
        )
        return super().resizeEvent(a0)

    def reloadUI(self):
        # 重新加载设置
        global config_dict, logger
        config_dict = pixiv_pyqt_tools.ConfigSetter.get_config(
            self.config_save_path)
        """
        # 弹出提示框
        info_box = QMessageBox()
        info_box.setWindowTitle("Pixiv")     # QMessageBox标题
        info_box.setText("重新加载窗口")      # QMessageBox的提示文字
        info_box.setStandardButtons(
            QMessageBox.StandardButton.Ok)      # QMessageBox显示的按钮

        info_box.button(QMessageBox.StandardButton.Ok).animateClick()
        info_box.exec()    # 如果使用.show(),会导致QMessageBox框一闪而逝
        time.sleep(1)
        # self.timer = QTimer(self)  # 初始化一个定时器
        """
        # 重新加载窗口
        self.destroy(True, True)
        self.setupUi()
        # 重新设置logger
        logger = MyLogging()
        logger.init(
            self.config_dict["enable_console_output"], self.tab.infodisplayer)
        logger.addHandler(console_handler)

    def creat_image_tab(self, image_data: dict | tuple):
        import GUI.tabs
        # print(image_data)
        if isinstance(image_data, dict):
            id = image_data.get("id")
            if len(image_data.get("relative_path")) == 1:
                tab = GUI.tabs.OriginalImageTab(image_data)
                tab.open_image(
                    self.config_dict["save_path"]+image_data.get("relative_path")[0])
            else:
                tab = GUI.tabs.ImageTab(self, self.config_dict["save_path"], logger, image_data,
                                        self.creat_image_tab, self.config_dict["use_thumbnail"])
            index = self.tabWidget.insertTab(2, tab, str(id))
        else:
            id = image_data[0]
            img_path = image_data[1]
            tab = GUI.tabs.OriginalImageTab()   # image_data[2]
            tab.open_image(self.config_dict["save_path"]+img_path)
            index = self.tabWidget.insertTab(self.tab_count - 3, tab, str(id))
        self.tabWidget.setCurrentIndex(index)
        self.tab_count += 1
        # self.tabWidget.addTab(tab, str(id))

    def close_tab(self, index):
        if index <= 1 or index >= (self.tab_count - 3):
            return
        self.tabWidget.removeTab(index)
        self.tabWidget.setCurrentIndex(index - 1)
        self.tab_count -= 1


if __name__ == "__main__":
    # 解决图片在不同分辨率显示模糊问题
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)  # 创建应用程序对象
    # 获取屏幕的缩放比例
    # list_screen = QApplication.screens()
    dpi = QApplication.primaryScreen().logicalDotsPerInch() / 96
    # scaleRate = QApplication.screens()[0].logicalDotsPerInch() / 96
    # print(scaleRate)
    # 日志记录
    logger = MyLogging()

    # main_window = mainwindow(dpi)  # 创建主窗口
    main_window = MainWindow(dpi)
    # 设置字体
    font = QFont()
    font.setPixelSize(14)
    # font.setPointSize(10)  # 括号里的数字可以设置成自己想要的字体大小
    font.setFamily("SimHei")  # 黑体
    # font.setFamily("SimSun")  # 宋体
    main_window.setFont(font)
    # main_window = QMainWindow()
    # ui = Ui_MainWindow()
    # ui.setupUi(main_window)
    # logger.init(ui.config_dict["enable_console_output"], ui.tab.infodisplayer)
    logger.init(
        main_window.config_dict["enable_console_output"], main_window.tab.infodisplayer)
    logger.addHandler(console_handler)
    main_window.setWindowFlags(Qt.WindowType.Window)
    # 显示一个非模式的对话框，用户可以随便切窗口，.exec()是模式对话框，用户不能随便切
    # ti = TrayIcon(main_window)
    # ti.show()
    main_window.show()  # 显示主窗口
    sys.exit(app.exec())  # 在主线程中退出
