# -*-coding:utf-8-*-
import os
import time
import asyncio
import pixiv_pyqt_tools
import infofetcher
import downloader
from PyQt6.QtCore import (
    QMetaObject,
    QObject,
    Qt,
    Q_ARG,
    QThread,
    QRunnable,
    pyqtSignal,
)
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel


class DownloadThreadingManger(QThread):
    break_signal = pyqtSignal()
    progress_signal = pyqtSignal(list)

    def __init__(self, config_dict: dict,  config_save_path,  db, backupcollection, logger) -> None:
        super().__init__()
        self.ifstop = False
        self.config_dict = config_dict
        self.config_save_path = config_save_path
        self.db = db
        self.backup_collection = backupcollection
        self.logger = logger

    def run(self):
        # 获取关注的作者
        if self.ifstop:
            return
        self.followings_recorder = pixiv_pyqt_tools.FollowingsRecorder(
            self.config_dict["cookies"], self.db, self.logger, self.progress_signal
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
            self.config_dict["last_record_time"], newtime
        ):
            self.info_getter = pixiv_pyqt_tools.InfoGetter(
                self.config_dict["cookies"],
                self.config_dict["download_type"],
                self.db,
                self.backup_collection,
                self.logger,
                self.progress_signal,
            )
            success = self.info_getter.start_get_info()
            if success:
                self.config_dict.update({"last_record_time": newtime})
                pixiv_pyqt_tools.ConfigSetter.set_config(
                    self.config_save_path, self.config_dict)
            del self.info_getter
        # 下载作品
        if self.ifstop:
            return
        self.downloader = pixiv_pyqt_tools.Downloader(
            self.config_dict["save_path"],
            self.config_dict["cookies"],
            self.config_dict["download_type"],
            self.config_dict["download_thread_number"],
            self.backup_collection,
            self.logger,
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

    def __init__(self, config_dict: dict,  config_save_path, db,
                 backupcollection, asyncdb, asyncbackupcollection, logger) -> None:
        super().__init__()
        self.ifstop = False
        self.config_dict = config_dict
        self.config_save_path = config_save_path
        self.db = db
        self.asyncdb = asyncdb
        self.backup_collection = backupcollection
        self.asyncbackup_collection = asyncbackupcollection
        self.logger = logger

    def run(self):
        proxies = (self.config_dict["http_proxies"], self.config_dict["https_proxies"])
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        newtime = time.strftime("%Y%m%d%H%M%S")
        if pixiv_pyqt_tools.Tools.compare_datetime(
            self.config_dict["last_record_time"], newtime
        ):
            # 获取关注的作者
            if self.ifstop:
                return
            self.followings_recorder = infofetcher.FollowingsRecorder(
                self.config_dict["cookies"], self.db, self.logger, self.progress_signal
            )
            self.followings_recorder.set_proxies(proxies)
            success = self.followings_recorder.following_recorder()
            if not success:
                self.break_signal.emit()
                return
            del self.followings_recorder
            # 获取关注的作者的信息
            if self.ifstop:
                return
            self.info_getter = infofetcher.InfoFetcherHttpx(
                self.config_dict["cookies"],
                self.config_dict["download_type"],
                self.asyncdb,
                self.asyncbackup_collection,
                self.logger,
                semaphore=self.config_dict["semaphore"]
            )
            self.info_getter.set_proxies(proxies)
            success = loop.run_until_complete(asyncio.ensure_future(
                self.info_getter.start_get_info()))
            if success:
                self.config_dict.update({"last_record_time": newtime})
                pixiv_pyqt_tools.ConfigSetter.set_config(
                    self.config_save_path, self.config_dict)
            del self.info_getter
        else:
            self.logger.info("最近已获取,跳过")
        # 下载作品
        if self.ifstop:
            return
        '''
        self.downloader = downloader.ThreadpoolDownloader(
            self.config_dict["save_path"],
            self.config_dict["cookies"],
            self.config_dict["download_type"],
            self.config_dict["download_thread_number"],
            self.backup_collection,
            self.logger,
        )
        self.downloader.set_proxies(proxies)
        self.downloader.start_following_download()
        '''
        self.downloader = downloader.AsyncioDownloaderHttpx(
            self.config_dict["save_path"],
            self.config_dict["cookies"],
            self.config_dict["download_type"],
            self.config_dict["semaphore"],
            self.asyncbackup_collection,
            self.logger,
        )
        loop.run_until_complete(asyncio.ensure_future(self.downloader.start_following_download()))
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
                os.remove(self.image_path)
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
