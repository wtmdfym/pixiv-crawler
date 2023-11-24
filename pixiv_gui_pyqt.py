# -*-coding:utf-8-*-
import logging
import os
import re
import sys
import time
import pymongo
import asyncio
import motor.motor_asyncio
import pixiv_pyqt_tools
import infofetcher
from PyQt6.QtCore import (
    QCoreApplication,
    QMetaObject,
    QObject,
    QRect,
    QSortFilterProxyModel,
    Qt,
    Q_ARG,
    pyqtSlot,
    QThread,
    QRunnable,
    QThreadPool,
    pyqtSignal,
)
from PyQt6.QtGui import QImage, QImageReader, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QCompleter,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

# 日志信息
logging.basicConfig(level=logging.INFO)
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
    def __init__(self, infodisplayer) -> None:
        super().__init__(self)
        if config_dict["enable_console_output"]:
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


class MainWindow(QMainWindow):
    def __init__(self, scaleRate) -> None:
        # 初始化设置信息
        global CONFIG_SAVE_PATH, config_dict
        CONFIG_SAVE_PATH = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "config.json"
        )
        config_dict = pixiv_pyqt_tools.ConfigSetter.get_config(
            CONFIG_SAVE_PATH)
        # 初始化数据库
        global db, backup_collection
        global asyncdb, asyncbackup_collection
        client = pymongo.MongoClient("localhost", 27017)
        asyncclient = motor.motor_asyncio.AsyncIOMotorClient(
            'localhost', 27017)
        db = client["pixiv"]
        asyncdb = asyncclient["pixiv"]
        backup_collection = client["backup"]["backup of pixiv infos"]
        asyncbackup_collection = asyncclient["backup"]["backup of pixiv infos"]
        super().__init__()
        self.scaleRate = scaleRate
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
        width = int(self.default_width * self.scaleRate)
        height = int(self.default_height * self.scaleRate)
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

    def setupUi(self):
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
        # 初始化MainTab
        self.tab = MainTab()
        self.tab.setObjectName("tab")
        self.tabWidget.addTab(self.tab, "")
        # 初始化SearchTab
        self.tab_1 = SearchTab()
        self.tab_1.setObjectName("tab_1")
        self.tabWidget.addTab(self.tab_1, "")
        # 初始化TagsTab
        self.tab_2 = TagsTab(
            changetab=self.tabWidget.setCurrentIndex,
            settext=self.tab_1.searchEdit.setText,
        )
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        # 初始化UserTab
        self.tab_3 = UserTab()
        self.tab_3.setObjectName("tab_3")
        self.tabWidget.addTab(self.tab_3, "")
        # 初始化ConfigsTab
        self.tab_4 = ConfigTab(self.reloadUI)
        self.tab_4.setObjectName("tab_4")
        self.tabWidget.addTab(self.tab_4, "")
        # 设置主窗口
        self.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(parent=self)
        self.menubar.setGeometry(QRect(0, 0, 768, 22))
        self.menubar.setObjectName("menubar")
        self.menuHelp = QMenu(parent=self.menubar)
        self.menuHelp.setObjectName("menuHelp")
        self.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(parent=self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)
        self.menubar.addAction(self.menuHelp.menuAction())

        self.retranslateUi()
        self.tabWidget.setCurrentIndex(1)
        # self.statusbar.showMessage
        QMetaObject.connectSlotsByName(self)

        """
        # 设置tab控件焦点
        self.setTabOrder(self.tabWidget, self.inpuEdit)
        self.setTabOrder(self.inpuEdit, self.startButton)
        self.setTabOrder(self.startButton, self.radioButton)
        self.setTabOrder(self.radioButton, self.radioButton_2)
        self.setTabOrder(self.radioButton_2, self.radioButton_3)
        self.setTabOrder(self.radioButton_3, self.searchEdit)
        self.setTabOrder(self.searchEdit, self.search_imageButton)
        self.setTabOrder(self.search_imageButton, self.images_tableWidget)
        self.setTabOrder(self.images_tableWidget, self.imageinfoDisplayer)
        self.setTabOrder(self.imageinfoDisplayer, self.prev_pageButton)
        self.setTabOrder(self.prev_pageButton, self.pageEdit)
        self.setTabOrder(self.pageEdit, self.jump_pageButton)
        self.setTabOrder(self.jump_pageButton, self.next_pageButton)
        self.setTabOrder(self.next_pageButton, self.search_tagEdit)
        self.setTabOrder(self.search_tagEdit, self.search_tagButton)
        self.setTabOrder(self.search_tagButton, self.addlikeButton)
        self.setTabOrder(self.addlikeButton, self.adddislikeButton)
        self.setTabOrder(self.adddislikeButton, self.select_tagButton)
        self.setTabOrder(self.select_tagButton, self.tags_tableWidget)
        self.setTabOrder(self.tags_tableWidget, self.scrollArea)
        self.setTabOrder(self.scrollArea, self.savepathEdit)
        self.setTabOrder(self.savepathEdit, self.cookiesEdit)
        self.setTabOrder(self.cookiesEdit, self.download_t_numberComboBox)
        self.setTabOrder(self.download_t_numberComboBox, self.getillustsCheckBox)
        self.setTabOrder(self.getillustsCheckBox, self.getmangaCheckBox)
        self.setTabOrder(self.getmangaCheckBox, self.getmangaSeriesCheckBox)
        self.setTabOrder(self.getmangaSeriesCheckBox, self.getnovelSeriesCheckBox)
        self.setTabOrder(self.getnovelSeriesCheckBox, self.getnovelsCheckBox)
        self.setTabOrder(self.getnovelsCheckBox, self.database_backupButton)
        self.setTabOrder(self.database_backupButton, self.save_configsButton)
        """

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
        self.tab_3.scrollArea.resize(
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
            CONFIG_SAVE_PATH)
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
        logger = MyLogging(self.tab.infodisplayer)
        logger.addHandler(console_handler)


class MainTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.default_width = 1240
        self.default_height = 700
        self.initUI()
        self.startButton.clicked.connect(self.start_download)
        self.download_method = "followings"
        # self.inpuEdit.textEdited['QString'].connect() # type: ignore

    def initUI(self):
        self.setObjectName("tab")
        self.setGeometry(QRect(0, 0, self.default_width, self.default_height))
        self.gridLayout_5 = QGridLayout(self)
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.inputEdit = QLineEdit(parent=self)
        self.inputEdit.setObjectName("inputEdit")
        self.gridLayout_5.addWidget(self.inputEdit, 0, 0, 1, 2)  # 位置0,0占1行2列
        self.startButton = QPushButton(parent=self)
        self.startButton.setObjectName("startButton")
        self.gridLayout_5.addWidget(self.startButton, 0, 2, 1, 1)
        self.radioButton = QRadioButton(parent=self)
        self.radioButton.setObjectName("radioButton")
        self.radioButton.toggled.connect(self.buttonStateRadio)
        self.gridLayout_5.addWidget(self.radioButton, 1, 0, 1, 1)
        self.radioButton_2 = QRadioButton(parent=self)
        self.radioButton_2.setObjectName("radioButton_2")
        self.radioButton_2.toggled.connect(self.buttonStateRadio)
        self.gridLayout_5.addWidget(self.radioButton_2, 1, 1, 1, 1)
        self.radioButton_3 = QRadioButton(parent=self)
        self.radioButton_3.setObjectName("radioButton_3")
        self.radioButton_3.setChecked(True)
        self.radioButton_3.toggled.connect(self.buttonStateRadio)
        self.gridLayout_5.addWidget(self.radioButton_3, 1, 2, 1, 1)
        self.progressBarLabellist = []
        self.progressBarlist = []
        for a in range(1, 2+1):  # config_dict['download_thread_number']+
            progressBarinfo = QLabel(parent=self)
            progressBarinfo.setText("No Process")
            self.gridLayout_5.addWidget(progressBarinfo, 0+a*2, 0, 1, 3)
            self.progressBarLabellist.append(progressBarinfo)
            self.progressBarlist.append(QProgressBar(parent=self))
            # self.progressBar.setMinimum(0)
            # self.progressBar.setMaximum(0)
            # self.progressBar.setTextVisible(False)
            # self.progressBar.setProperty("value", 99)
            # self.progressBar.setObjectName("progressBar")
            self.gridLayout_5.addWidget(
                self.progressBarlist[a-1], 1+a*2, 0, 1, 3)
        self.infodisplayer = QTextBrowser(parent=self)
        self.gridLayout_5.addWidget(
            self.infodisplayer, 4+(config_dict['download_thread_number']+1)*2, 0, 1, 3)

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.inputEdit.setPlaceholderText(
            _translate("MainWindow", "输入要下载的作品id或标签"))
        self.startButton.setText(_translate("MainWindow", "Start"))
        self.radioButton.setText(_translate("MainWindow", "Onework"))
        self.radioButton_2.setText(_translate("MainWindow", "Tags"))
        self.radioButton_3.setText(_translate("MainWindow", "Followings"))

    def buttonStateRadio(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            self.download_method = radioButton.text()

    @pyqtSlot(list)
    def update_progressBar(self, infolist):
        for a in range(len(infolist)):
            info = infolist[a]
            if info:
                self.progressBarLabellist[a].setText(info[0])
                self.progressBarlist[a].setValue(info[1])

    def start_download(self):
        self.startButton.setDisabled(True)
        if self.download_method == "work":
            downloader = pixiv_pyqt_tools.Downloader(
                config_dict["save_path"],
                config_dict["cookies"],
                config_dict["download_type"],
                config_dict["download_thread_number"],
                backup_collection,
            )
            downloader.start_work_download(id=self.inputEdit.text())
        elif self.download_method == "followings":
            # self.t = DownloadThreadingManger()
            self.t = AsyncDownloadThreadingManger()
            self.t.progress_signal.connect(self.update_progressBar)
            self.t.break_signal.connect(self.stop_download)
            self.t.start()
            self.startButton.setText("stop")
            self.startButton.clicked.disconnect(self.start_download)
            self.startButton.clicked.connect(self.stop_download)
        self.startButton.setEnabled(True)

    def stop_download(self):
        """
        调用线程管理器方法,停止所有线程
        """
        self.startButton.setDisabled(True)
        try:
            self.t.stop()
            self.startButton.setText("start")
            self.startButton.clicked.disconnect(self.stop_download)
            self.startButton.clicked.connect(self.start_download)
        except Exception:
            pass
        finally:
            self.startButton.setEnabled(True)


class DownloadThreadingManger(QThread):
    break_signal = pyqtSignal()
    progress_signal = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__()
        self.ifstop = False

    def run(self):
        global config_dict
        # 获取关注的作者
        if self.ifstop:
            return
        self.followings_recorder = pixiv_pyqt_tools.FollowingsRecorder(
            config_dict["cookies"], db, logger, self.progress_signal
        )
        success = self.followings_recorder.following_recorder()
        if not success:
            self.break_signal.emit()
            return
        del self.followings_recorder
        # 获取关注的作者的信息
        if self.ifstop:
            return
        newtime = time.strftime("%Y%m%d%H%M%S")
        if pixiv_pyqt_tools.Tools.compare_datetime(
            config_dict["last_record_time"], newtime
        ):
            self.info_getter = pixiv_pyqt_tools.InfoGetter(
                config_dict["cookies"],
                config_dict["download_type"],
                db,
                backup_collection,
                logger,
                self.progress_signal,
            )
            success = self.info_getter.start_get_info()
            if success:
                config_dict.update({"last_record_time": newtime})
                pixiv_pyqt_tools.ConfigSetter.set_config(
                    CONFIG_SAVE_PATH, config_dict)
            del self.info_getter
        # 下载作品
        if self.ifstop:
            return
        self.downloader = pixiv_pyqt_tools.Downloader(
            config_dict["save_path"],
            config_dict["cookies"],
            config_dict["download_type"],
            config_dict["download_thread_number"],
            backup_collection,
            logger,
            self.progress_signal,
        )
        self.downloader.start_following_download()
        del self.downloader
        self.break_signal.emit()

    def stop(self):
        self.ifstop = True
        try:
            self.followings_recorder.stop_recording()
        except AttributeError:
            pass
        try:
            self.info_getter.stop_getting()
        except AttributeError:
            pass
        try:
            self.downloader.stop_downloading()
        except AttributeError:
            pass
        self.quit()


class AsyncDownloadThreadingManger(QThread):
    break_signal = pyqtSignal()
    progress_signal = pyqtSignal(list)

    def __init__(self) -> None:
        super().__init__()
        self.ifstop = False

    def run(self):
        global config_dict
        newtime = time.strftime("%Y%m%d%H%M%S")
        if pixiv_pyqt_tools.Tools.compare_datetime(
            config_dict["last_record_time"], newtime
        ):
            # 获取关注的作者
            if self.ifstop:
                return
            self.followings_recorder = infofetcher.FollowingsRecorder(
                config_dict["cookies"], db, logger, self.progress_signal
            )
            success = self.followings_recorder.following_recorder()
            if not success:
                self.break_signal.emit()
                return
            del self.followings_recorder
            # 获取关注的作者的信息
            if self.ifstop:
                return
            self.info_getter = infofetcher.InfoGetter(
                config_dict["cookies"],
                config_dict["download_type"],
                asyncdb,
                asyncbackup_collection,
                logger,
                semaphore=2
            )
            success = asyncio.run(self.info_getter.start_get_info_async())
            if success:
                config_dict.update({"last_record_time": newtime})
                pixiv_pyqt_tools.ConfigSetter.set_config(
                    CONFIG_SAVE_PATH, config_dict)
            del self.info_getter
        else:
            logger.info("最近已获取,跳过")
        """
        # 下载作品
        if self.ifstop:
            return
        self.downloader = pixiv_pyqt_tools.Downloader(
            config_dict["save_path"],
            config_dict["cookies"],
            config_dict["download_type"],
            config_dict["download_thread_number"],
            backup_collection,
            logger,
            self.progress_signal,
        )
        self.downloader.start_following_download()
        del self.downloader
        """
        self.break_signal.emit()

    def stop(self):
        self.ifstop = True
        try:
            self.followings_recorder.stop_recording()
        except AttributeError:
            pass
        try:
            self.info_getter.stop_getting()
        except AttributeError:
            pass
        try:
            self.downloader.stop_downloading()
        except AttributeError:
            pass
        self.quit()


class SearchTab(QWidget):
    def __init__(self):
        super().__init__()
        self.page = 1
        self.total_page = 1
        self.save_path = config_dict["save_path"]
        self.image_url = "https://www.pixiv.net/"
        self.image_path = self.save_path + "picture/"
        self.default_width = 1220
        self.default_height = 700
        self.initUI()

    def initUI(self):
        self.setObjectName("tab_1")
        self.setGeometry(QRect(0, 0, self.default_width, self.default_height))
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout_2")
        # 搜索控件
        self.searchEdit = QLineEdit(parent=self)
        self.searchEdit.setObjectName("searchEdit")
        self.gridLayout.addWidget(self.searchEdit, 0, 0, 1, 2)
        self.search_imageButton = QPushButton(parent=self)
        self.search_imageButton.setObjectName("search_imageButton")
        self.search_imageButton.clicked.connect(self.search)
        self.gridLayout.addWidget(self.search_imageButton, 0, 2, 1, 1)
        # 在浏览器和资源管理器中显示
        self.show_in_browserButton = QPushButton(parent=self)
        self.show_in_browserButton.setObjectName("show_in_browserButton")
        self.show_in_browserButton.clicked.connect(self.show_in_browser)
        self.gridLayout.addWidget(self.show_in_browserButton, 1, 0, 1, 3)
        self.show_in_resourceButton = QPushButton(parent=self)
        self.show_in_resourceButton.setObjectName("show_in_resourceButton")
        self.show_in_resourceButton.clicked.connect(self.show_in_resource)
        self.gridLayout.addWidget(self.show_in_resourceButton, 2, 0, 1, 3)
        # 显示控件
        self.imageinfoDisplayer = QTextBrowser(parent=self)
        self.imageinfoDisplayer.setObjectName("imageinfoDisplayer")
        # self.imageinfoDisplayer.setFixedHeight(600)
        self.gridLayout.addWidget(self.imageinfoDisplayer, 3, 0, 1, 3)
        self.imagedisplatLayout = QVBoxLayout()
        self.images_tableWidget = ImageTableWidget(
            parent=self, save_path=self.save_path, callback=self.update_image_info
        )
        self.imagedisplatLayout.addWidget(self.images_tableWidget, 0)
        # self.gridLayout.addWidget(self.images_tableWidget, 0, 3, 2, 1)
        # 翻页控件
        self.pageLayout = QHBoxLayout()
        self.prev_pageButton = QPushButton(parent=self)
        self.prev_pageButton.setObjectName("prev_pageButton")
        self.prev_pageButton.setMaximumWidth(100)
        self.prev_pageButton.clicked.connect(
            lambda: self.change_page(page=self.page - 1)
        )
        self.pageLayout.addWidget(self.prev_pageButton, 0)
        self.pageEdit = QSpinBox(parent=self)
        self.pageEdit.setMaximumWidth(100)
        self.pageEdit.setMinimum(1)
        self.pageEdit.setMaximum(self.total_page)
        self.pageLayout.addWidget(self.pageEdit, 1)
        self.pageLabel = QLabel(parent=self)
        self.pageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pageLabel.setObjectName("pageLabel")
        self.pageLabel.setMaximumWidth(100)
        self.pageLayout.addWidget(self.pageLabel, 2)
        self.jump_pageButton = QPushButton(parent=self)
        self.jump_pageButton.setObjectName("jump_pageButton")
        self.jump_pageButton.setMaximumWidth(100)
        self.jump_pageButton.clicked.connect(
            lambda: self.change_page(page=self.pageEdit.value())
        )
        self.pageLayout.addWidget(self.jump_pageButton, 3)
        self.next_pageButton = QPushButton(parent=self)
        self.next_pageButton.setObjectName("next_pageButton")
        self.next_pageButton.setMaximumWidth(100)
        self.next_pageButton.clicked.connect(
            lambda: self.change_page(page=self.page + 1)
        )
        self.pageLayout.addWidget(self.next_pageButton, 4)
        self.imagedisplatLayout.addLayout(self.pageLayout, 1)
        self.gridLayout.addLayout(self.imagedisplatLayout, 0, 3, 5, 1)
        # self.gridLayout.addLayout(self.pageLayout, 3, 3, 1, 1)

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.searchEdit.setPlaceholderText(
            _translate("MainWindow", "输入要搜索的标签"))
        self.imageinfoDisplayer.setPlaceholderText(
            _translate("MainWindow", "单击图片获取图片信息\n双击查看大图"))
        self.jump_pageButton.setText(_translate("MainWindow", "Jump"))
        self.pageLabel.setText(_translate("MainWindow", "No Page"))
        self.next_pageButton.setText(_translate("MainWindow", "Next Page"))
        self.prev_pageButton.setText(_translate("MainWindow", "Prev Page"))
        self.search_imageButton.setText(_translate("MainWindow", "Search"))
        self.show_in_browserButton.setText(
            _translate("MainWindow", "Show in browser"))
        self.show_in_resourceButton.setText(
            _translate("MainWindow", "Show in resource")
        )

    def search(self):
        self.page, self.total_page = self.images_tableWidget.search(
            self.searchEdit.text()
        )
        self.pageEdit.setMaximum(self.total_page)
        self.pageLabel.setText(str(self.page) + "/" + str(self.total_page))

    def update_image_info(self, image_info, image_url, image_path):
        self.image_url, self.image_path = image_url, image_path
        self.imageinfoDisplayer.setText(image_info)

    def show_in_browser(self):
        import webbrowser

        webbrowser.open(self.image_url)

    def show_in_resource(self):
        file = self.save_path + self.image_path
        file = os.path.realpath(file)
        # print(file)
        if os.path.exists(file):
            logger.info("文件路径:%s" % file)
            os.system(f"explorer /select, {file}")
        else:
            # print("文件不存在:%s"%(file))
            logger.warning("文件不存在:%s" % (file))

    def change_page(self, page):
        if page == 0:
            return
        elif page > self.total_page:
            return
        self.page = page
        self.pageEdit.setValue(self.page)
        self.pageLabel.setText(str(page) + "/" + str(self.total_page))
        self.images_tableWidget.change_page(page)

    def resizeEvent(self, a0) -> None:
        new_width = self.width()
        new_height = self.height()
        width_ratio = new_width / self.default_width
        height_ratio = new_height / self.default_height
        self.images_tableWidget.img_width = int(
            self.images_tableWidget.default_img_width * width_ratio
        )
        self.images_tableWidget.img_height = int(
            self.images_tableWidget.default_img_height * height_ratio
        )
        self.images_tableWidget.resize(
            self.images_tableWidget.img_width * self.images_tableWidget.columns + 10,
            self.images_tableWidget.img_height * self.images_tableWidget.rows + 10,
        )
        return super().resizeEvent(a0)


class ImageTableWidget(QTableWidget):
    def __init__(self, parent, save_path, callback):
        super().__init__(parent)
        self.save_path = save_path
        self.callback = callback
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
        self.use_thumbnail = config_dict.get("use_thumbnail")
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
                label = QLabel()
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
        self.itemSelectionChanged.connect(self.update_image_info)
        self.image_datas = []

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
            self.results = backup_collection.find(
                {"$and": and_search}).sort("id", -1)

        elif re.findall(r"\,", search_info):
            or_search = []
            for one_search in search_info.split(","):
                if re.search(r"\d{4,}", one_search):
                    or_search.append({"userId": one_search})
                else:
                    or_search.append(
                        {"tags." + one_search: {"$exists": "true"}})
                self.results = backup_collection.find(
                    {"$or": or_search}).sort("id", -1)

        elif search_info:
            one_search = {}
            if re.search(r"\d{4,}", search_info):
                one_search.update({"userId": search_info})
            else:
                one_search.update({"tags." + search_info: {"$exists": "true"}})
            self.results = backup_collection.find(one_search).sort("id", -1)

        else:
            self.results = backup_collection.find(
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
                    logger.warning("加载图片失败:" + relative_path)
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

    def update_image_new(self):
        self.image_load_pool.clear()
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
            logger.warning("加载图片失败!")
        elif code == 3:
            label.setText("Not download")
        elif code == 0:
            label.setPixmap(pixmap)
        # QApplication.processEvents()

    def update_image_info(self):
        try:
            index = self.selectedIndexes()[0]
        except IndexError:
            self.callback("", self.img_url, self.img_path)
            return
        index = index.row() * self.columns + index.column()
        try:
            result = self.images[index]
        except IndexError:
            self.callback("", "", "")
            return
        except AttributeError:
            self.callback("", "", "")
            return
        id = result.get("id")
        type = result.get("type")
        title = result.get("title")
        userid = result.get("userId")
        username = result.get("username")
        description = result.get("description")
        self.img_url = "https://www.pixiv.net/artworks/" + str(id)
        self.img_path = result.get("relative_path")[0]

        infos = "ID:{}\nType:{}\nTitle:{}\nUserID:{}\nUserName:{}\nDescription:\n{}"
        self.callback(
            infos.format(id, type, title, userid, username, description),
            self.img_url,
            self.img_path,
        )

    def change_page(self, page):
        self.page = page
        self.clearSelection()
        self.update_image_new()

    def resizeEvent(self, e) -> None:
        return super().resizeEvent(e)
        # 设置单元格宽高
        for i in range(self.rows):  # 让行高和图片相同
            self.setRowHeight(i, self.img_height)
        for i in range(self.columns):  # 让列宽和图片相同
            self.setColumnWidth(i, self.img_width)


class TagsTab(QWidget):
    def __init__(self, changetab, settext):
        super().__init__()
        self.tags_collection = db["All Tags"]
        self.like_tag_collection = db["Like Tag"]
        self.dislike_tag_collection = db["Dislike Tag"]
        self.finded_tags_count = 0
        self.changetab = changetab
        self.settext = settext
        self.default_width = 1220
        self.default_height = 700
        self.initUI()
        # 加载标签
        self.load_tags()
        # 事件绑定
        self.tags_tableWidget.itemSelectionChanged.connect(self.fill_comboBox)
        self.search_tagComboBox.lineEdit().textEdited.connect(self.search_tag)
        # self.search_tagButton.clicked.connect(self.search_tag)
        self.select_tagButton.clicked.connect(self.select_tag)
        self.addlikeButton.clicked.connect(self.addlike)
        self.adddislikeButton.clicked.connect(self.adddislike)
        self.delete_tagButton.clicked.connect(self.delete_tag)

    def initUI(self):
        self.setObjectName("tab_2")
        self.setGeometry(QRect(0, 0, self.default_width, self.default_height))
        self.gridLayout_3 = QGridLayout(self)
        self.gridLayout_3.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_3.setObjectName("gridLayout_3")
        # self.search_tagEdit = QLineEdit(parent=self)
        # self.search_tagEdit.setObjectName("search_tagEdit")
        # self.gridLayout_3.addWidget(self.search_tagEdit, 0, 0, 1, 1)
        self.search_tagComboBox = ExtendedComboBox(parent=self)
        self.search_tagComboBox.setObjectName("search_tagComboBox")
        self.gridLayout_3.addWidget(self.search_tagComboBox, 0, 0, 1, 2)
        # self.search_tagButton = QPushButton(parent=self)
        # self.search_tagButton.setObjectName("search_tagButton")
        # self.gridLayout_3.addWidget(self.search_tagButton, 0, 1, 1, 1)
        self.select_tagButton = QPushButton(parent=self)
        self.select_tagButton.setObjectName("select_tagButton")
        self.gridLayout_3.addWidget(self.select_tagButton, 0, 2, 1, 1)
        self.addlikeButton = QPushButton(parent=self)
        self.addlikeButton.setObjectName("addlikeButton")
        self.gridLayout_3.addWidget(self.addlikeButton, 0, 3, 1, 1)
        self.adddislikeButton = QPushButton(parent=self)
        self.adddislikeButton.setObjectName("adddislikeButton")
        self.gridLayout_3.addWidget(self.adddislikeButton, 0, 4, 1, 1)
        self.delete_tagButton = QPushButton(parent=self)
        self.delete_tagButton.setObjectName("delete_tagButton")
        self.gridLayout_3.addWidget(self.delete_tagButton, 0, 5, 1, 1)
        self.tags_tableWidget = QTableWidget(parent=self)
        self.tags_tableWidget.setObjectName("tags_tableWidget")
        self.tags_tableWidget.setColumnCount(3)
        self.tags_tableWidget.setColumnWidth(0, 300)
        self.tags_tableWidget.setColumnWidth(1, 300)
        self.tags_tableWidget.setColumnWidth(2, 300)
        # 禁止编辑
        self.tags_tableWidget.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        # 选择方式
        self.tags_tableWidget.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        # 自定义第一行内容
        self.tags_tableWidget.setHorizontalHeaderLabels(
            ["All", "Like", "Dislike"])
        self.gridLayout_3.addWidget(self.tags_tableWidget, 1, 0, 1, 6)

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        # self.search_tagButton.setText(_translate("MainWindow", "search"))
        self.search_tagComboBox.setPlaceholderText(
            _translate("MainWindow", "输入要搜索的标签"))
        self.select_tagButton.setText(_translate("MainWindow", "select"))
        self.addlikeButton.setText(_translate("MainWindow", "addlike"))
        self.adddislikeButton.setText(_translate("MainWindow", "adddislike"))
        self.delete_tagButton.setText(_translate("MainWindow", "delete"))

    def load_tags(self):
        tags = (
            self.tags_collection.find({"works_number": {"$gt": 5}}, {"_id": 0})
            .sort("works_number", -1)
            .limit(500)
        )
        count = self.tags_collection.count_documents(
            {"works_number": {"$gt": 5}}, limit=500
        )
        self.tags_tableWidget.setRowCount(count)
        row = 0
        for tag in tags:
            table_data = str((tag.get("name"), tag.get("translate")))
            self.tags_tableWidget.setItem(row, 0, QTableWidgetItem(table_data))
            row += 1
        tags.close()
        tags = self.like_tag_collection.find(
            {"name": {"$exists": "true"}}, {"_id": 0})
        self.likerow = 0
        for tag in tags:
            table_data = str((tag.get("name"), tag.get("translate")))
            self.tags_tableWidget.setItem(
                self.likerow, 1, QTableWidgetItem(table_data))
            self.likerow += 1
        tags.close()
        tags = self.dislike_tag_collection.find(
            {"name": {"$exists": "true"}}, {"_id": 0}
        )
        self.dislikerow = 0
        for tag in tags:
            table_data = str((tag.get("name"), tag.get("translate")))
            self.tags_tableWidget.setItem(
                self.dislikerow, 2, QTableWidgetItem(table_data)
            )
            self.dislikerow += 1
        tags.close()

    def fill_comboBox(self):
        try:
            text = self.tags_tableWidget.selectedItems()[0].text()
        except IndexError:
            text = ""
        self.search_tagComboBox.setEditText(text)

    def select_tag(self):
        selected_tag = self.search_tagComboBox.currentText()
        selected_tag = eval(selected_tag)
        self.changetab(1)
        self.settext(selected_tag[0])

    def delete_tag(self):
        selected_tag = self.tags_tableWidget.selectedItems()[0]
        selection = eval(selected_tag.text())
        name, a = selection
        if selected_tag.column() == 1:
            selected_tag.setText("")
            self.like_tag_collection.find_one_and_delete({"name": name})
        elif selected_tag.column() == 2:
            selected_tag.setText("")
            self.dislike_tag_collection.find_one_and_delete({"name": name})
        elif selected_tag.column() == 0:
            # print("Don't delete tag in All tags!")
            logger.info("Don't delete tag in All tags!")

    def addlike(self):
        selected = self.tags_tableWidget.selectedItems()[0].text()
        selected_tag = eval(selected)
        earlier = self.like_tag_collection.find_one({"name": selected_tag[0]})
        if earlier:
            if earlier != {"name": selected_tag[0], "translate": selected_tag[1]}:
                self.like_tag_collection.find_one_and_update(
                    {"name": selected_tag[0]}, {
                        "$set": {"translate": selected_tag[1]}}
                )
        else:
            self.like_tag_collection.insert_one(
                {"name": selected_tag[0], "translate": selected_tag[1]}
            )
            self.tags_tableWidget.setItem(
                self.likerow, 1, QTableWidgetItem(selected))
            self.likerow += 1

    def adddislike(self):
        selected = self.tags_tableWidget.selectedItems()[0].text()
        selected_tag = eval(selected)
        earlier = self.dislike_tag_collection.find_one(
            {"name": selected_tag[0]})
        if earlier:
            if earlier != {"name": selected_tag[0], "translate": selected_tag[1]}:
                self.dislike_tag_collection.find_one_and_update(
                    {"name": selected_tag[0]}, {
                        "$set": {"translate": selected_tag[1]}}
                )
        else:
            self.dislike_tag_collection.insert_one(
                {"name": selected_tag[0], "translate": selected_tag[1]}
            )
            self.tags_tableWidget.setItem(
                self.dislikerow, 2, QTableWidgetItem(selected)
            )
            self.dislikerow += 1

    def finder(self):
        def fuzzy_finder(key, data):
            """
            模糊查找器
            :param key: 关键字
            :param data: 数据
            :return: list
            """
            # 结果列表
            suggestions = []
            # 非贪婪匹配，转换 'djm' 为 'd.*?j.*?m'
            # pattern = '.*?'.join(key)
            pattern = ".*%s.*" % (key)
            # print("pattern",pattern)
            # 编译正则表达式
            regex = re.compile(pattern)
            for item in data:
                # 检查当前项是否与regex匹配。
                match = regex.search(str(item))
                if match:
                    # 如果匹配，就添加到列表中
                    suggestions.append(item)
            return suggestions

        result_list = []
        for one in self.quary.get():
            result_list = list(set(result_list) | set(
                fuzzy_finder(one, self.all_tags)))
        print(result_list)

    def search_tag(self, text):
        # text = self.search_tagEdit.text()
        for a in range(self.finded_tags_count):
            self.search_tagComboBox.removeItem(a)
        # print(text)
        if text:
            findeditems = self.tags_tableWidget.findItems(
                text, Qt.MatchFlag.MatchContains
            )
            findedtags = []
            for findeditem in findeditems:
                findedtags.append(findeditem.text())
            self.finded_tags_count = len(findedtags)
            self.search_tagComboBox.addItems(findedtags)
        else:
            self.finded_tags_count = 0
        self.search_tagComboBox.setEditText(text)
        self.search_tagComboBox.pFilterModel.setFilterFixedString(text)
        # print(findedtags)


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


class UserTab(QWidget):
    def __init__(self):
        super().__init__()
        self.default_width = 1220
        self.default_height = 700
        self.initUI()

    def initUI(self):
        self.setObjectName("tab_3")
        self.scrollArea = ScrollArea(parent=self)
        self.scrollArea.setGeometry(
            QRect(0, 0, self.default_width, self.default_height)
        )
        self.scrollArea.setObjectName("scrollArea")


class ScrollArea(QScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        self.all_users = []
        for one in db["All Followings"].find(
            {"userId": {"$exists": "true"}}, {"_id": 0}
        ):
            self.all_users.append(one)
        self.page = 1
        self.pagesize = 8
        self.total_page = (
            db["All Followings"].count_documents(
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
            logger.warning("加载图片失败!")
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
            collection = db[user_info["userName"]]
            for one in (
                collection.find(
                    {"id": {"$exists": "true"}}, {"_id": 0, "relative_path": 1}
                )
                .sort("id", -1)
                .limit(4)
            ):
                relative_path = one.get("relative_path")[0]
                if config_dict["use_thumbnail"]:
                    relative_path = re.search(
                        "(?<=picture/).*", relative_path).group()
                    path = config_dict["save_path"] + \
                        "thumbnail/" + relative_path
                else:
                    path = config_dict["save_path"] + relative_path
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
                    logger.warning("加载图片失败:" + relative_path)
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
            collection = db[user_info["userName"]]
            for one in (
                collection.find(
                    {"id": {"$exists": "true"}}, {"_id": 0, "relative_path": 1}
                )
                .sort("id", -1)
                .limit(4)
            ):
                relative_path = one.get("relative_path")[0]
                if config_dict["use_thumbnail"]:
                    relative_path = re.search(
                        "(?<=picture/).*", relative_path).group()
                    path = config_dict["save_path"] + \
                        "thumbnail/" + relative_path
                else:
                    path = config_dict["save_path"] + relative_path
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


class ConfigTab(QWidget):
    def __init__(self, reloadUI):
        super().__init__()
        self.default_width = 1220
        self.default_height = 700
        self.reloadUIcall = reloadUI
        self.initUI()
        # 显示设置信息
        self.savepathEdit.setText(config_dict.get("save_path"))
        self.cookiesEdit.setPlainText(str(config_dict.get("cookies")))
        self.enable_console_outputCheckBox.setChecked(
            config_dict.get("enable_console_output"))
        self.enable_thumbnailCheckBox.setChecked(
            config_dict.get("use_thumbnail"))
        self.semaphoreComboBox.setCurrentIndex(
            config_dict.get("semaphore") - 1
        )
        self.download_thread_numberComboBox.setCurrentIndex(
            config_dict.get("download_thread_number") - 1
        )
        download_type = config_dict.get("download_type")
        for a in download_type.items():
            if a[0] == "getillusts" and a[1]:
                self.getillustsCheckBox.setChecked(True)
            elif a[0] == "getmanga" and a[1]:
                self.getmangaCheckBox.setChecked(True)
            elif a[0] == "getmangaSeries" and a[1]:
                self.getmangaSeriesCheckBox.setChecked(True)
            elif a[0] == "getnovelSeries" and a[1]:
                self.getnovelSeriesCheckBox.setChecked(True)
            elif a[0] == "getnovels" and a[1]:
                self.getnovelsCheckBox.setChecked(True)

        # 设置事件绑定
        self.save_configsButton.clicked.connect(self.save_configs)
        self.reloadUIButton.clicked.connect(self.reloadUIcall)
        self.database_backupButton.clicked.connect(self.mongoDB_manual_backup)
        self.generate_thumbnailButton.clicked.connect(self.generate_thumbnail)
        # self.generate =self.GenerateThumbnail(self.update_progressBar)
        # self.generate_thumbnailButton.clicked.connect(self.generate.run)

    def initUI(self):
        self.setObjectName("tab_4")
        self.setGeometry(QRect(0, 0, self.default_width, self.default_height))
        self.gridLayout = QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        # 保存路径
        self.pathLabel = QLabel(parent=self)
        self.pathLabel.setObjectName("pathLabel")
        self.gridLayout.addWidget(self.pathLabel, 0, 0, 1, 1)
        self.savepathEdit = QLineEdit(parent=self)
        self.savepathEdit.setObjectName("savepathEdit")
        self.gridLayout.addWidget(self.savepathEdit, 0, 1, 1, 2)
        # cookie
        self.cookieLabel = QLabel(parent=self)
        self.cookieLabel.setObjectName("cookieLabel")
        self.gridLayout.addWidget(self.cookieLabel, 1, 0, 1, 1)
        self.cookiesEdit = QPlainTextEdit(parent=self)
        self.cookiesEdit.setObjectName("cookiesEdit")
        self.gridLayout.addWidget(self.cookiesEdit, 1, 1, 1, 2)
        # 启用控制台输出
        self.enable_console_outputCheckBox = QCheckBox(parent=self)
        self.gridLayout.addWidget(
            self.enable_console_outputCheckBox, 2, 0, 1, 3)
        # 缩略图
        self.enable_thumbnailCheckBox = QCheckBox(parent=self)
        self.gridLayout.addWidget(self.enable_thumbnailCheckBox, 3, 0, 1, 1)
        self.generate_thumbnailButton = QPushButton(parent=self)
        self.gridLayout.addWidget(self.generate_thumbnailButton, 3, 1, 1, 2)
        # 最大并发数
        self.semaphoreLabel = QLabel(parent=self)
        self.gridLayout.addWidget(self.semaphoreLabel, 4, 0, 1, 1)
        self.semaphoreComboBox = QComboBox(parent=self)
        self.semaphoreComboBox.setObjectName(
            "download_t_numberComboBox")
        self.semaphoreComboBox.addItem("")
        self.semaphoreComboBox.addItem("")
        self.semaphoreComboBox.addItem("")
        self.semaphoreComboBox.addItem("")
        self.semaphoreComboBox.addItem("")
        self.semaphoreComboBox.addItem("")
        self.gridLayout.addWidget(
            self.semaphoreComboBox, 4, 1, 1, 2)
        # 下载线程数
        self.download_t_numberLabel = QLabel(parent=self)
        self.download_t_numberLabel.setObjectName("download_t_numberLabel")
        self.gridLayout.addWidget(self.download_t_numberLabel, 5, 0, 1, 1)
        self.download_thread_numberComboBox = QComboBox(parent=self)
        self.download_thread_numberComboBox.setObjectName(
            "download_t_numberComboBox")
        self.download_thread_numberComboBox.addItem("")
        self.download_thread_numberComboBox.addItem("")
        self.download_thread_numberComboBox.addItem("")
        self.download_thread_numberComboBox.addItem("")
        self.gridLayout.addWidget(
            self.download_thread_numberComboBox, 5, 1, 1, 2)
        # 下载作品类型
        self.download_typeLabel = QLabel(parent=self)
        self.download_typeLabel.setObjectName("download_typeLabel")
        self.gridLayout.addWidget(self.download_typeLabel, 6, 0, 1, 3)
        self.getillustsCheckBox = QCheckBox(parent=self)
        self.getillustsCheckBox.setObjectName("getillustsCheckBox")
        self.gridLayout.addWidget(self.getillustsCheckBox, 7, 0, 1, 3)
        self.getmangaCheckBox = QCheckBox(parent=self)
        self.getmangaCheckBox.setObjectName("getmangaCheckBox")
        self.gridLayout.addWidget(self.getmangaCheckBox, 8, 0, 1, 3)
        self.getmangaSeriesCheckBox = QCheckBox(parent=self)
        self.getmangaSeriesCheckBox.setObjectName("getmangaSeriesCheckBox")
        self.gridLayout.addWidget(self.getmangaSeriesCheckBox, 9, 0, 1, 3)
        self.getnovelSeriesCheckBox = QCheckBox(parent=self)
        self.getnovelSeriesCheckBox.setObjectName("getnovelSeriesCheckBox")
        self.gridLayout.addWidget(self.getnovelSeriesCheckBox, 10, 0, 1, 3)
        self.getnovelsCheckBox = QCheckBox(parent=self)
        self.getnovelsCheckBox.setObjectName("getnovelsCheckBox")
        self.gridLayout.addWidget(self.getnovelsCheckBox, 11, 0, 1, 3)
        # 保存按钮
        self.save_configsButton = QPushButton(parent=self)
        self.save_configsButton.setObjectName("save_configsButton")
        self.gridLayout.addWidget(self.save_configsButton, 12, 0, 1, 1)
        # 重载GUI界面按钮
        self.reloadUIButton = QPushButton(parent=self)
        self.reloadUIButton.setObjectName("reloadUIButton")
        self.gridLayout.addWidget(self.reloadUIButton, 12, 1, 1, 1)
        # 数据库备份按钮
        self.database_backupButton = QPushButton(parent=self)
        self.database_backupButton.setObjectName("database_backupButton")
        self.gridLayout.addWidget(self.database_backupButton, 12, 2, 1, 1)

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.pathLabel.setText(_translate("MainWindow", "save path"))
        self.cookieLabel.setText(_translate("MainWindow", "cookies"))
        self.enable_console_outputCheckBox.setText(
            _translate("MainWindow", "启用控制台输出"))
        self.enable_thumbnailCheckBox.setText(
            _translate("MainWindow", "使用缩略图"))
        self.generate_thumbnailButton.setText(
            _translate("MainWindow", "生成缩略图"))
        self.semaphoreLabel.setText(_translate(
            "MainWindow", "最大并发数(若过高可能被封IP,封号......)"))
        self.semaphoreComboBox.setItemText(
            0, _translate("MainWindow", "1")
        )
        self.semaphoreComboBox.setItemText(
            1, _translate("MainWindow", "2")
        )
        self.semaphoreComboBox.setItemText(
            2, _translate("MainWindow", "3")
        )
        self.semaphoreComboBox.setItemText(
            3, _translate("MainWindow", "4")
        )
        self.semaphoreComboBox.setItemText(
            4, _translate("MainWindow", "5")
        )
        self.semaphoreComboBox.setItemText(
            5, _translate("MainWindow", "6")
        )
        self.download_t_numberLabel.setText(_translate("MainWindow", "下载线程数"))
        self.download_thread_numberComboBox.setItemText(
            0, _translate("MainWindow", "1")
        )
        self.download_thread_numberComboBox.setItemText(
            1, _translate("MainWindow", "2")
        )
        self.download_thread_numberComboBox.setItemText(
            2, _translate("MainWindow", "3")
        )
        self.download_thread_numberComboBox.setItemText(
            3, _translate("MainWindow", "4")
        )
        self.download_typeLabel.setText(_translate("MainWindow", "下载作品类型"))
        self.getillustsCheckBox.setText(_translate("MainWindow", "Getillusts"))
        self.getmangaCheckBox.setText(_translate("MainWindow", "Getmanga"))
        self.getmangaSeriesCheckBox.setText(
            _translate("MainWindow", "GetmangaSeries"))
        self.getnovelSeriesCheckBox.setText(
            _translate("MainWindow", "GetnovelSeries"))
        self.getnovelsCheckBox.setText(_translate("MainWindow", "Getnovels"))
        self.save_configsButton.setText(_translate("MainWindow", "save"))
        self.reloadUIButton.setText(_translate("MainWindow", "reloadUI"))
        self.database_backupButton.setText(
            _translate("MainWindow", "backup database"))

    def save_configs(self):
        global config_dict
        new_config_dict = {}
        new_config_dict["save_path"] = self.savepathEdit.text()
        cookies = self.cookiesEdit.toPlainText()
        new_config_dict["cookies"] = config_dict.get("cookies")
        if not re.search("{.*}", cookies):
            new_config_dict["cookies"] = pixiv_pyqt_tools.Tools.analyze_cookie(
                cookies)
            self.cookiesEdit.setPlainText(str(new_config_dict["cookies"]))
        new_config_dict["enable_console_output"] = self.enable_console_outputCheckBox.isChecked()
        new_config_dict["use_thumbnail"] = self.enable_thumbnailCheckBox.isChecked()
        new_config_dict["semaphore"] = (
            self.semaphoreComboBox.currentIndex() + 1
        )
        new_config_dict["download_thread_number"] = (
            self.download_thread_numberComboBox.currentIndex() + 1
        )
        download_type = {}
        download_type["getillusts"] = self.getillustsCheckBox.isChecked()
        download_type["getmanga"] = self.getmangaCheckBox.isChecked()
        download_type["getmangaSeries"] = self.getmangaSeriesCheckBox.isChecked()
        download_type["getnovelSeries"] = self.getnovelSeriesCheckBox.isChecked()
        download_type["getnovels"] = self.getnovelsCheckBox.isChecked()
        new_config_dict["download_type"] = download_type
        new_config_dict["last_record_time"] = config_dict["last_record_time"]
        if new_config_dict != config_dict:
            pixiv_pyqt_tools.ConfigSetter.set_config(
                CONFIG_SAVE_PATH, new_config_dict)
            msgBox = QMessageBox.information(
                self, "INFO", "重新加载窗口以应用设置?", buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            if msgBox == QMessageBox.StandardButton.Ok:
                self.reloadUIcall()

    def mongoDB_manual_backup(self):
        # print("开始手动备份,请勿关闭程序!!!")
        logger.info("开始手动备份,请勿关闭程序!!!")
        now = 1
        all = len(db.list_collection_names())
        for name in db.list_collection_names():
            break
            print("正在备份第%d/%d个数据库" % (now, all))
            collection = db[name]
            a = collection.find({"id": {"$exists": True}}, {"_id": 0})
            for docs in a:
                if len(docs) == 9:
                    b = backup_collection.find_one({"id": docs.get("id")})
                    if b:
                        if b.get("failcode"):
                            del b["failcode"]
                        if b == docs:
                            continue
                        else:
                            c = backup_collection.find_one_and_update(
                                {"id": docs.get("id")}, {"$set": docs}
                            )
                        if c:
                            pass
                        else:
                            print("cao")
                            print(docs)
                    else:
                        backup_collection.insert_one(docs)
            done = int(50 * now / all)
            sys.stdout.write(
                "\r[%s%s] %d%%" % ("█" * done, " " *
                                   (50 - done), 100 * now / all)
            )
            sys.stdout.flush()
            now += 1
        # print("手动备份完成")
        logger.info("手动备份完成")

    def generate_thumbnail(self):
        self.progressDialog = QProgressDialog("准备读取数据库......", "取消", 0, 101)
        self.progressDialog.setWindowTitle("生成缩略图......")
        self.progressDialog.setFixedSize(500, 100)
        self.progressDialog.show()
        self.t = self.GenerateThumbnail()
        self.t.progress_signal.connect(self.updateProgressDialog)
        self.progressDialog.canceled.connect(self.t.stop)
        self.progressDialog.destroyed.connect(self.t.stop)
        self.t.start()

    def updateProgressDialog(self, text, value):
        self.progressDialog.setLabelText(text)
        self.progressDialog.setValue(value)

    class GenerateThumbnail(QThread):
        progress_signal = pyqtSignal(str, int)

        def __init__(self) -> None:
            super().__init__()
            self.ifstop = False

        def run(self) -> None:
            from PIL import Image, UnidentifiedImageError

            save_path = config_dict["save_path"]
            now = 1
            collist = db.list_collection_names()
            all = len(collist) - 4
            for name in collist:
                if name == "All Followings":
                    continue
                elif name == "All Tags":
                    continue
                elif name == "Like Tag":
                    continue
                elif name == "Dislike Tag":
                    continue
                # print("\n正在读取第%d/%d个数据库:%s"%(now,all,name))
                logger.debug("正在读取第%d/%d个数据库:%s" % (now, all, name))
                # progressDialog.setLabelText("正在读取数据库:%s" % name)
                now1 = 1
                collection = db[name]
                docs = collection.find({"id": {"$exists": True}}, {"_id": 0})
                all1 = collection.count_documents({"id": {"$exists": True}})
                for doc in docs:
                    uid = doc.get("userId")
                    if not uid:
                        continue
                    paths = doc.get("relative_path")
                    if not os.path.exists(save_path + "thumbnail/" + uid):
                        os.mkdir(save_path + "thumbnail/" + uid)
                    for path in paths:
                        if self.ifstop:
                            break
                        picture_path = save_path + path
                        thumbnail_path = (
                            save_path
                            + "thumbnail/"
                            + re.search("(?<=picture/).*", path).group()
                        )
                        if os.path.exists(picture_path):
                            if not os.path.exists(thumbnail_path):
                                try:
                                    loaded_image = Image.open(picture_path)
                                    loaded_image.load()
                                except UnidentifiedImageError:
                                    os.remove(picture_path)
                                    continue
                                except OSError:
                                    loaded_image.close()
                                    os.remove(picture_path)
                                    continue
                                original_width, original_height = loaded_image.size
                                aspect_ratio = original_width / original_height
                                if aspect_ratio > 1:
                                    new_width = min(original_width, 320)
                                    new_height = int(new_width / aspect_ratio)
                                else:
                                    new_height = min(original_height, 360)
                                    new_width = int(new_height * aspect_ratio)
                                resized_image = loaded_image.resize(
                                    (new_width, new_height))
                                resized_image.save(thumbnail_path)
                    if self.ifstop:
                        break
                    self.progress_signal.emit(
                        "正在读取数据库:%s" % name, int(100 * now1 / all1))
                    now1 += 1
                if self.ifstop:
                    logger.info("停止生成缩略图")
                    return
                now += 1
            logger.info("生成缩略图完成")
            self.progress_signal.emit("生成缩略图完成", 100)

        def stop(self):
            self.ifstop = True


class ImageLoader(QRunnable):
    """
    读取图片并异步返回给主线程
    """

    def __init__(self, obj: QObject, img_width: int, img_height: int,
                 target: QLabel = None, index: tuple = None, image_path: str = None):
        super().__init__()
        self.qobject = obj
        self.img_width = img_width
        self.img_height = img_height
        self.target = target
        self.index = index
        self.image_path = image_path

    def run(self):
        if os.path.exists(self.image_path):
            image = QImage(self.image_path)
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
                args = (0, pixmap)
            else:
                args = (2, None)
        else:
            args = (3, None)
        # 加载完成后异步发送
        if self.index:
            QMetaObject.invokeMethod(self.qobject, 'set_image', Qt.ConnectionType.QueuedConnection, Q_ARG(
                tuple, self.index), Q_ARG(object, args))
        elif self.target:
            QMetaObject.invokeMethod(self.qobject, 'set_image', Qt.ConnectionType.QueuedConnection, Q_ARG(
                QLabel, self.target), Q_ARG(object, args))


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
    main_window = MainWindow(dpi)  # 创建主窗口
    main_window.setupUi()
    logger = MyLogging(main_window.tab.infodisplayer)
    logger.addHandler(console_handler)
    main_window.show()  # 显示主窗口
    sys.exit(app.exec())  # 在主线程中退出

    import requests
    from tqdm import tqdm

    url = "https://example.com/large_file"
    file_size = 100 * 1024 * 1024  # 假设文件大小为100MB

    response = requests.get(url, stream=True)

    total_length = file_size
    current_length = 0

    with open("output.file", "wb") as f:
        for chunk in tqdm(
            response.iter_content(chunk_size=1024),
            total=total_length // 1024,
            unit="KB",
        ):
            current_length += 1024
            f.write(chunk)
            done = int(50 * current_length // file_size)
            print(
                ("\r[%s%s] %d%%")
                % (("=" * done), " " * (50 - done), 100 * current_length // file_size),
                end="",
            )

    # 在这个示例中，我们使用`tqdm`包装`requests`的`iter_content`方法，以便在下载文件时显示进度条。
