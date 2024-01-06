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

    def __init__(self, config_dict: dict,  config_save_path, db,    # loop,
                 backupcollection, asyncdb, asyncbackupcollection, logger) -> None:
        super().__init__()
        self.ifstop = False
        self.config_dict = config_dict
        self.config_save_path = config_save_path
        # self.loop = loop
        self.db = db
        self.asyncdb = asyncdb
        self.backup_collection = backupcollection
        self.asyncbackup_collection = asyncbackupcollection
        self.logger = logger

    def run(self):
        proxies = (self.config_dict["http_proxies"],
                   self.config_dict["https_proxies"])
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        newtime = time.strftime("%Y%m%d%H%M%S")
        if pixiv_pyqt_tools.Tools.compare_datetime(
            self.config_dict["last_record_time"], newtime
        ):
            # 获取关注的作者
            if self.ifstop:
                loop.stop()
                return
            self.followings_recorder = infofetcher.FollowingsRecorder(
                self.config_dict["cookies"], self.db, self.logger, self.progress_signal
            )
            self.followings_recorder.set_proxies(proxies)
            success = self.followings_recorder.following_recorder()
            if not success:
                self.break_signal.emit()
                loop.stop()
                return
            del self.followings_recorder
            # 获取关注的作者的信息
            if self.ifstop:
                loop.stop()
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
            loop.stop()
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
        loop.run_until_complete(asyncio.ensure_future(
            self.downloader.start_following_download()))
        del self.downloader
        self.break_signal.emit()
        loop.stop()

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
                # 图片加载成功
                args = (0, pixmap)
            else:
                # 图片加载失败
                os.remove(self.image_path)
                args = (2, None)
        else:
            # 图片不存在
            args = (3, None)
        # 加载完成后异步发送
        if self.index:
            QMetaObject.invokeMethod(self.qobject, 'set_image', Qt.ConnectionType.QueuedConnection, Q_ARG(
                tuple, self.index), Q_ARG(object, args))
        elif self.target:
            QMetaObject.invokeMethod(self.qobject, 'set_image', Qt.ConnectionType.QueuedConnection, Q_ARG(
                QLabel, self.target), Q_ARG(object, args))


import pymongo
class Searcher():
    def __init__(self, search_criteria, client: pymongo.MongoClient) -> None:
        '''TODO series and novels'''
        self.client = client
        # {'keywords': {'all': '捆绑,R-18', 'some': '', 'no': 'ai'},
        #  'worktype': 0, 'searchtype': 0, 'integratework': False}
        # :/runoob/
        query = {}
        orquery = []
        # 搜索的作品类型
        # worktype [0:"插画、漫画、动图(动态漫画)", 1:"插画、动图", 2:"插画", 3:"漫画", 4:"动图"]
        worktype = search_criteria.get("worktype")
        worktypeindex = [{'type': 'illust'}, {
            'type': 'manga'}, {'type': 'ugoira'}]
        if worktype == 0:
            typequery = [worktypeindex[0], worktypeindex[1], worktypeindex[2]]
            typequery = {'$or': typequery}
        elif worktype == 1:
            typequery = [worktypeindex[0], worktypeindex[2]]
            typequery = {'$or': typequery}
        elif worktype == 2:
            typequery = worktypeindex[0]
        elif worktype == 3:
            typequery = worktypeindex[1]
        elif worktype == 3:
            typequery = worktypeindex[2]

        self.keywords = search_criteria.get("keywords")
        if isinstance(self.keywords, dict):
            keywords_type = ["AND", "OR", "NOT"]
            type_map = {"AND": ''}
            keywords = {}
            for key in keywords_type:
                _keyword = self.keywords.get(key)
                if _keyword:
                    _keyword = _keyword.split(',')
                keyword = _keyword[0]
                if len(_keyword) >= 1:
                    for one in _keyword[1:]:
                        keyword += f' {key} \"{one}\"'
                keywords.update({key: keyword})
        else:
            _keyword = self.keywords.split(',')
            keyword = _keyword[0]
            if len(_keyword) >= 1:
                for one in _keyword[1:]:
                    keyword += f' OR \"{one}\"'
        self.keywords = keywords
        self.search_type = search_criteria.get("searchtype")

    def get_result(self):
        # searchtype [0:"标签(部分一致)", 1:"标签(完全一致)", 2:"标题、说明文字"]
        if self.search_type == 0:
            result = self.search_by_tag()
        elif self.search_type == 1:
            result = self.search_by_tag(partly=False)
        elif self.search_type == 2:
            result = self.search_by_title_or_description

    def search_by_tag(self, partly=True):
        # {'$text': { '$search': }
        collection = self.client['pixiv']['All Tags']
        if partly:
            if isinstance(self.keywords, dict):
                pass
            else:
                pass
            for one in self.keywords.split(','):
                pass
            collection.find(query).sort("id", -1)
        else:
            pass

    def search_by_title_or_description(self):
        pass

    def search_by_userId(self):
        pass

    def search_by_content(self):
        pass
