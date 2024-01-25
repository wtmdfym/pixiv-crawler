# -*-coding:utf-8-*-
import threading
import requests


class FollowingsRecorder:
    """Get information about users you've followed



    Attributes:
        __version: Parameters in the Pixiv request link (usefulness unknown)
        __proxies: Proxy to use requests to send HTTP requests (optional)
        __event: The stop event
        cookies: The cookies when a request is sent to pixiv
        db: Database of MongoDB
        logger: The instantiated object of logging.Logger
        progress_signal: The pyqtSignal of QProgressBar
        headers: The headers when sending a HTTP request to pixiv
    """
    __version = '54b602d334dbd7fa098ee5301611eda1776f6f39'
    __proxies = {'http': 'http://localhost:1111',
                 'https': 'http://localhost:1111'}
    __event = threading.Event()

    def __init__(self, cookies: dict, database, logger, progress_signal):
        """Initialize followingrecoder class

        Initialize class variables and stop event

        Args:
            cookies(dict):The cookies of pixiv
            database(Database):Database of MongoDB
            logger(:class:`logging.Logger`):The instantiated object of logging.Logger
            progress_singal(:class:`PyQt6.QtCore.pyqtSignal`):The pyqtSignal of QProgressBar
        """
        self.cookies = cookies
        self.db = database
        self.logger = logger
        self.progress_signal = progress_signal
        self.headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
            "referer": "https://www.pixiv.net/"}
        self.__event.set()

    def following_recorder(self):
        """Get information about users you've followed

            Visit Pixiv to get the users you following, and then
            call the __get_my_followings method to get the author information.
            After the acquisition is complete, it is added to the MongoDB database

            Args:
                None

            Returns:
                1: The function has been successfully executed

            Raises:
                Exception: The database operation failed
        """
        self.logger.info("获取已关注的用户的信息......")
        url = "https://www.pixiv.net/ajax/user/extra?lang=zh&version={version}".format(
            version=self.__version
        )
        # self.headers.update(
        #     {"referer": "https://www.pixiv.net/users/83945559/following?p=1"})
        with requests.Session() as session:
            try:
                response1 = session.get(
                    url=url,
                    headers=self.headers,
                    cookies=self.cookies,
                    proxies=self.__proxies,
                    timeout=3,
                )
            except requests.exceptions.ConnectionError:
                self.logger.error("无法访问pixiv,检查你的网络连接")
                return
                # raise Exception('[ERROR]-----无法访问pixiv,检查你的网络连接')
            try:
                response = response1.json()
            except requests.exceptions.JSONDecodeError:
                self.logger.error("无法访问pixiv,检查你的网络连接\n%s" % response1)
                return
                # raise Exception('[ERROR]-----无法访问pixiv,检查你的网络连接')
            if response.get("error"):
                self.logger.error(
                    "请检查你的cookie是否正确\ninformation:%s\nyour cookies:%s"
                    % (response, self.cookies)
                )
                return
                # raise Exception('请检查你的cookie是否正确',response)
            if not self.__event.is_set():
                return
            body = response.get("body")
            following = body.get("following")
            following_infos = self.__get_my_followings(session, following)
            # print(followings)
            session.close()

        if not self.__event.is_set():
            return
        self.logger.info("开始更新数据库......")
        followings_collection = self.db["All Followings"]
        # 记录当前关注的作者信息
        userId_list = []
        info_count = len(following_infos)
        for count in range(info_count):
            following = following_infos[count]
            userId = following.get("userId")
            userId_list.append(userId)
            # 跳过Pixiv官方的账户
            if userId == "11":
                continue
            earlier = followings_collection.find_one({"userId": userId})
            userName = following.get("userName")
            userComment = following.get("userComment")
            if earlier:
                self.logger.debug(
                    "Have been recorded:%s" % (
                        {"userId": userId, "userName": userName})
                )
                earlier_userName = earlier.get("userName")
                earlier_userComment = earlier.get("userComment")
                if earlier_userName != userName:
                    self.logger.debug(
                        "Updating:%s to %s" % (earlier_userName, userName)
                    )
                    self.__rename_collection(earlier_userName, userName)
                    # make sure update is successful
                    result = followings_collection.update_one(
                        {"userId": userId}, {"$set": {"userName": userName}}
                    )
                    if result:
                        self.logger.debug("Update Success")
                    else:
                        raise Exception("update failed")
                if earlier_userComment != userComment:
                    self.logger.debug("Updating userComment......")
                    result = followings_collection.update_one(
                        {"userId": userId}, {"$set": {"userComment": userComment}}
                    )
                    # make sure update is successful
                    if result:
                        self.logger.debug("Update Success")
                    else:
                        raise Exception("Update Failed")
            else:
                self.logger.debug(
                    "recording:{}".format(
                        {"userId": userId, "userName": userName})
                )
                result = followings_collection.insert_one(
                    {"userId": userId, "userName": userName,
                        "userComment": userComment}
                )
                # make sure update is successful
                if result:
                    self.logger.debug("Insert Success")
                else:
                    raise Exception("Insert Failed")
            self.progress_signal.emit(
                [("更新数据库......", int(100 * count / info_count))])
        # 检查是否有已取消关注的作者
        # {"userId": {"$exists": "true"}}
        earliers = list(followings_collection.find())
        count = 0
        info_count = len(earliers)
        for earlier in earliers:
            userId = earlier.get("userId")
            userName = earlier.get("userName")
            if userId in userId_list:
                pass
            else:
                followings_collection.find_one_and_update(
                    {"userId": userId}, {'$set': {'not_following_now': True}})
                print("已取消关注:%s" % {"userId": userId, "userName": userName})
            self.progress_signal.emit(
                [("检查数据库......", int(100 * count / info_count))])
        self.progress_signal.emit([("更新数据库完成", 100)])
        self.logger.info("更新数据库完成")
        return 1

    def __get_my_followings(self, session: requests.Session, following: int):
        """Get the user's information

            Get the user's username, ID, and self-introduction

            Args:
                following(int):Number of users followed

            Returns:
                A list of usernames, IDs, and self-introductions for each author you follow. For example:

                [{'userId': '75793178', 'userName': '木下林檎', 'userComment': '努力自学画画小小萌新，画风不定多变，大佬们多多关照啦~'},
                    {'userId': '21752034', 'userName': 'Flanling', 'userComment': '連絡方法が知りたい方はピクシブまでお問い合わせください
                    原稿受付を一時停止しますContact me on pixiv to get  information.Temporarily stop accepting manuscripts
                    luoyeyingdie@gmail.com'}]

        """
        following_url = "https://www.pixiv.net/ajax/user/83945559/following?offset={offset}\
            &limit=24&rest=show&tag=&acceptingRequests=0&lang=zh&version={version}"
        userinfos = []
        all_page = following // 24 + 1
        for page in range(all_page):
            if not self.__event.is_set():
                self.progress_signal.emit([("No Process", 100)])
                return
            self.progress_signal.emit(
                [("获取关注作者页......", int(100 * (page + 1)/all_page))])
            # sys.stdout.write("\r获取关注作者页%d/%d" % (page + 1, all_page))
            # sys.stdout.flush()
            # self.headers.update(
            #     {"referer": "https://www.pixiv.net/users/83945559/following?p=%d" % page})
            following_url1 = following_url.format(
                offset=page * 24, version=self.__version)
            error_count = 0
            while 1:
                response = 0
                try:
                    response = session.get(
                        url=following_url1,
                        headers=self.headers,
                        cookies=self.cookies,
                        proxies=self.__proxies,
                        timeout=3,
                    ).json()
                except requests.exceptions.ConnectionError:
                    self.logger.warning("连接超时!  请检查你的网络!")
                    error_count += 1
                    if error_count == 4:
                        self.logger.info("自动重试失败!")
                        return None
                    self.logger.info("自动重试---%d/3" % error_count)
                finally:
                    if response is not None and response != 0:
                        if error_count:
                            self.logger.info("自动重试成功!")
                        break
            body = response.get("body")
            users = body.get("users")
            for user in users:
                userId = user.get("userId")
                userName = user.get("userName")
                userComment = user.get("userComment")
                userinfos.append(
                    {"userId": userId, "userName": userName,
                        "userComment": userComment}
                )
        self.logger.info("获取关注作者完成")
        self.progress_signal.emit([("No Process", 100)])
        return userinfos

    def __rename_collection(self, name1: str, name2: str) -> None:
        """Rename the MongoDB collection

        Rename the collection when the author you follow changes the name

        Args:
            name1(str): The original name of a collection
            name2(str): The new name of a collection

        Returns:
            None
        """
        self.logger.debug("重命名数据库......")
        collection_1 = self.db[name1]
        collection_2 = self.db[name2]
        for doc in collection_1.find({"id": {"$exists": True}}):
            # print(doc)
            doc.update({"username": name2})
            collection_2.insert_one(doc)
        collection_1.drop()

    def set_proxies(self, proxies: tuple):
        http_proxies = proxies[0]
        https_proxies = proxies[1]
        self.__proxies.update({'http': http_proxies, 'https': https_proxies})

    def stop_recording(self) -> None:
        """Stop the function from running

        Via :class:`threading.Event` to send a stop event

        Args:
            None

        Returns:
            None
        """
        self.__event.clear()
        self.logger.info("停止获取关注的作者信息")
