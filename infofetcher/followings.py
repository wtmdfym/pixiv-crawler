# -*-coding:utf-8-*-
import threading
import requests


class FollowingsRecorder:
    """
    用于获取已关注的用户的信息



    Attributes:
        __version: Pixiv请求链接中带有的参数(用处暂时未知)
        __proxies:用requests发送http请求时用的代理(可选)
        __event:The stop event
        cookies:The cookies when a request is sent to pixiv
        db:Database of MongoDB
        logger:The instantiated object of logging.Logger
        progress_signal:The pyqtSignal of QProgressBar
        headers:The headers when sending a request to pixiv
    """
    __version = ''
    __proxies = ''
    __event = threading.Event()

    def __init__(self, cookies: dict, database, logger, progress_signal):
        """initialize followingrecoder class

        初始化类变量,停止事件

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
        """获取已关注的用户的信息

            访问Pixiv获取关注的用户,然后调用__get_my_followings
            方法获取作者信息。获取完毕后添加到MongoDB数据库中

            Args:
                None

            Returns:
                1:函数成功执行完毕

            Raises:
                Exception: 数据库操作失败
        """
        self.logger.info("获取已关注的用户的信息......")
        url = "https://www.pixiv.net/ajax/user/extra?lang=zh&version={version}".format(
            version=self.__version
        )
        # self.headers.update(
        #     {"referer": "https://www.pixiv.net/users/83945559/following?p=1"})
        try:
            response1 = requests.get(
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
        following_infos = self.__get_my_followings(following)
        if not self.__event.is_set():
            return
        # print(followings)
        self.logger.info("开始更新数据库......")
        followings_collection = self.db["All Followings"]
        info_count = len(following_infos)
        for count in range(info_count):
            following = following_infos[count]
            userId = following.get("userId")
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
                result = self.followings_collection.insert_one(
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
        self.progress_signal.emit([("No Process", 100)])
        self.logger.info("更新数据库完成")
        return 1

    def __get_my_followings(self, following: int):
        """获取用户的信息

            获取用户的用户名、ID以及自我介绍

            Args:
                following(int):关注的用户数目

            Returns:
                一个列表,包含了关注的每个作者的用户名、ID以及自我介绍。例如:

                [{'userId': '53184612', 'userName': '水星すい☪︎*', 'userComment': '水星すいですいつもイラストを見ていただきありがとうございます*ﾟ
                    アイコン等のイラスト使用につきましては一言お声かけていただければ基本許可しております。
                    (無断転載、自作発言等はお控えください)pixivでのご連絡には対応が遅れてし
                    まうため、御手数ですがTwitterのDMでお声をかけていただけますと幸いです。Twitter→@suisei_1121
                    pixivFANBOX→ https://www.fanbox.cc/manage/relationships今後ともよろしくお願いいたします🙇\u200d♂️'},
                    {'userId': '75793178', 'userName': '木下林檎', 'userComment': '努力自学画画小小萌新，画风不定多变，大佬们多多关照啦~'},
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
            response = requests.get(
                url=following_url1,
                headers=self.headers,
                cookies=self.cookies,
                proxies=self.__proxies,
                timeout=3,
            ).json()
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
        """重命名MongoDB的集合

        当关注的作者更改名字时重命名集合

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

    def stop_recording(self) -> None:
        """停止函数运行

        通过 :class:`threading.Event` 发送停止事件

        Args:
            None

        Returns:
            None
        """
        self.__event.clear()
        self.logger.info("停止获取关注的作者信息")
