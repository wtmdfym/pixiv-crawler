# -*-coding:utf-8-*-
import glob
import html
import json
import os
import re
import threading
import time
import zipfile
import aiohttp
import asyncio
import http.cookies
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib import parse

import requests
import urllib3.exceptions
from PIL import Image

http.cookies._is_legal_key = lambda _: True
urllib3.disable_warnings()

# 代理
proxie = ""

version = "12bf979348f8a251a88224d94a7ba55705d943fe"

CONFIG_PATH = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "config.json")


class Analyzer:
    def __init__(self, database_client) -> None:
        self.db = database_client["pixiv"]

    def tag_to_url(tag) -> str:
        """URL编码"""
        url = parse.quote(tag)
        return url

    def failure_recoder_mongo(self, id: int):
        collection = self.db["failures"]
        if collection.find_one({"id": id}):
            # print('错误已记录')
            pass
        else:
            res = collection.insert_one({"id": id})
            if res:
                pass
                # print('记录错误成功')

    def analyze_input(input_info) -> list:
        if not input_info:
            return None
        uids = []
        tags = []
        infos1 = input_info
        if re.search("，", infos1):
            # print('输入格式错误!!!')
            return None
        infos = infos1.split(",")
        for info in infos:
            uid = re.search("[0-9]+", info)
            if uid is not None:
                uids.append(uid.group())
            else:
                tags.append(info)
        if len(uids) and len(tags):
            # print('输入格式错误!!!')
            return None
        return [uids, tags]


class ConfigSetter:
    def __init__(self) -> None:
        pass

    @classmethod
    def get_config(cls, config_file_path: str) -> dict:
        with open(config_file_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)
        return config_dict

    @classmethod
    def set_config(cls, config_file_path: str, config_dict: dict) -> None:
        with open(config_file_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=4)


class FollowingsRecorder:
    """
    获取已关注的用户的信息
    """

    def __init__(self, cookies, database, logger, progress_signal):
        self.cookies = cookies
        self.db = database
        self.logger = logger
        self.progress_signal = progress_signal
        self.headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
            "referer": "https://www.pixiv.net/"}
        self.followings_collection = database["All Followings"]
        self.event = threading.Event()
        self.event.set()

    def following_recorder(self):
        self.logger.info("获取已关注作者的信息......")
        url = "https://www.pixiv.net/ajax/user/extra?lang=zh&version={version}".format(
            version=version
        )
        # self.headers.update(
        #     {"referer": "https://www.pixiv.net/users/83945559/following?p=1"})
        try:
            response1 = requests.get(
                url=url,
                headers=self.headers,
                cookies=self.cookies,
                proxies=proxie,
                verify=False,
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
        if not self.event.is_set():
            return
        body = response.get("body")
        following = body.get("following")
        following_infos = self.get_my_followings(following)
        if not self.event.is_set():
            return
        # print(followings)
        self.logger.info("开始更新数据库......")
        info_count = len(following_infos)
        for count in range(info_count):
            following = following_infos[count]
            userId = following.get("userId")
            if userId == "11":
                continue
            earlier = self.followings_collection.find_one({"userId": userId})
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
                    self.rename_collection(earlier_userName, userName)
                    # make sure update is successful
                    a = self.followings_collection.update_one(
                        {"userId": userId}, {"$set": {"userName": userName}}
                    )
                    if a:
                        self.logger.debug("Update Success")
                    else:
                        raise Exception("update failed")
                if earlier_userComment != userComment:
                    self.logger.debug("Updating userComment......")
                    a = self.followings_collection.update_one(
                        {"userId": userId}, {"$set": {"userComment": userComment}}
                    )
                    if a:
                        self.logger.debug("Update Success")
                    else:
                        raise Exception("Update Failed")
            else:
                self.logger.debug(
                    "recording:{}".format(
                        {"userId": userId, "userName": userName})
                )
                self.followings_collection.insert_one(
                    {"userId": userId, "userName": userName,
                        "userComment": userComment}
                )
            self.progress_signal.emit(
                [("更新数据库......", int(100 * count / info_count))])
        self.progress_signal.emit([("No Process", 100)])
        self.logger.info("更新数据库完成")
        return 1

    def get_my_followings(self, following):
        following_url = "https://www.pixiv.net/ajax/user/83945559/following?offset={offset}\
            &limit=24&rest=show&tag=&acceptingRequests=0&lang=zh&version={version}"
        userinfos = []
        all_page = following // 24 + 1
        for page in range(all_page):
            if not self.event.is_set():
                self.progress_signal.emit([("No Process", 100)])
                return
            self.progress_signal.emit(
                [("获取关注作者页......", int(100 * (page + 1)/all_page))])
            # sys.stdout.write("\r获取关注作者页%d/%d" % (page + 1, all_page))
            # sys.stdout.flush()
            # self.headers.update(
            #     {"referer": "https://www.pixiv.net/users/83945559/following?p=%d" % page})
            following_url1 = following_url.format(
                offset=page * 24, version=version)
            response = requests.get(
                url=following_url1,
                verify=False,
                headers=self.headers,
                cookies=self.cookies,
                proxies=proxie,
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

    def rename_collection(self, name1, name2):
        """
        当关注的作者更改名字时重命名集合
        :name1 原来的集合名字
        :name2 新的集合名字
        """
        self.logger.debug("重命名数据库......")
        collection_1 = self.db[name1]
        collection_2 = self.db[name2]
        for doc in collection_1.find({"id": {"$exists": True}}):
            # print(doc)
            doc.update({"username": name2})
            collection_2.insert_one(doc)
        collection_1.drop()

    def stop_recording(self):
        self.event.clear()
        time.sleep(0.5)
        self.logger.info("停止获取关注的作者")


class InfoGetter:
    """
    获取作品信息
    """

    def __init__(self, cookies: str, download_type: dict, db, backup_collection, logger,
                 semaphore: int = None, progress_signal=None) -> None:
        self.db = db
        self.cookies = cookies
        self.download_type = download_type
        self.backup_collection = backup_collection
        self.logger = logger
        self.progress_signal = progress_signal
        self.headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
            "referer": "https://www.pixiv.net/"}
        self.timeout = aiohttp.ClientTimeout(total=5)
        self.semaphore = asyncio.Semaphore(semaphore)
        self.event = threading.Event()
        self.event.set()

    def start_get_info(self):
        finish = self.record_infos()
        if finish:
            success = self.mongoDB_auto_backup()
            if success:
                return True
            else:
                raise Exception("database backup error")

    async def start_get_info_async(self):
        finish = await self.record_infos_async()
        if finish:
            success = await self.mongoDB_auto_backup_async()
            if success:
                return True
            else:
                raise Exception("database backup error")

    def record_infos(self):
        self.followings_collection = self.db["All Followings"]
        painters = self.followings_collection.find(
            {"userId": {"$exists": True}})
        painters_count = self.followings_collection.count_documents(
            {"userId": {"$exists": True}})
        now = 0
        for painter in painters:
            uid = painter.get("userId")
            name = painter.get("userName")
            self.logger.info("获取%s(uid:%s)的作品信息......" % (name, uid))
            collection = self.db[name]
            ids = self.get_id(uid=uid)
            if ids:
                self.record_info_mongodb(name, ids=ids, collection=collection)
            if not self.event.is_set():
                return False
            now += 1
            self.progress_signal.emit(
                [("获取作者作品信息......", int(100 * now / painters_count))])
        self.progress_signal.emit([0, 0])
        self.logger.info("获取所有作者的作品信息完成")
        return True

    async def record_infos_async(self):

        def ids_callback(future):
            # 这里默认传入一个future对象
            name, ids = future.result()
            if ids:
                self.record_info_mongodb_async(
                    name, ids=ids, collection=self.db[name])
        async with self.semaphore:
            async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies, timeout=self.timeout) as session:
                self.followings_collection = self.db["All Followings"]
                painters = self.followings_collection.find(
                    {"userId": {"$exists": True}})
                task_list = []
                async for painter in painters:
                    # for painter in painters:
                    uid = painter.get("userId")
                    name = painter.get("userName")
                    ids = self.bound_get_id_async(session, user=(uid, name))
                    task = asyncio.create_task(ids)
                    # task.add_done_callback(ids_callback)
                    task_list.append(task)
                    # break
                futurelist = await asyncio.gather(*task_list)
                if not self.event.is_set():
                    return False
                for future in futurelist:
                    if future:
                        name, ids = future
                        # print(name)
                        if ids:
                            # print("ok")
                            await self.record_info_mongodb_async(ids=ids, session=session, collection=self.db[name])
        self.logger.info("获取所有作者的作品信息完成")
        return True

    def get_id(self, tag=None, uid=None) -> dict:
        """获取作者所有作品的id"""
        failure = False
        Ids = {}
        if tag is not None:
            pass

            # All_Ids['tag'] = Ids
            # 等待，防止封IP
            time.sleep(1)

        elif uid is not None:
            # self.logger.info("获取作者{}的作品id".format(uid))
            self.headers.update(
                {"referer": "https://www.pixiv.net/users/{}".format(uid)})
            xhr_url = (
                "https://www.pixiv.net/ajax/user/{}/profile/all?lang=zh&version={}".format(
                    uid, version)
            )
            try:
                ids_json = requests.get(
                    xhr_url,
                    headers=self.headers,
                    cookies=self.cookies,
                    proxies=proxie,
                    verify=False,
                ).json()
            except Exception:
                self.logger.error("获取ID失败")
                for a in range(1, 4):
                    self.logger.info("自动重试---%d/3" % a)
                    time.sleep(3)
                    try:
                        ids_json = requests.get(
                            xhr_url,
                            headers=self.headers,
                            cookies=self.cookies,
                            proxies=proxie,
                            verify=False,
                        ).json()
                        if ids_json is not None:
                            self.logger.info("自动重试成功!")
                            break
                    except Exception:
                        self.logger.info("自动重试失败!")
                        if a == 3:
                            failure = True
            if failure:
                return None
            body = ids_json.get("body")
            if type(body) is not dict:
                # raise Exception('[ERROR]获取ID失败!',body)
                # print("[ERROR]获取ID失败!")
                # print(ids_json)
                self.logger.error("获取ID失败!\nIds:%s" % str(ids_json))
                return None
            # 插图
            illusts = []
            illusts1 = body.get("illusts")
            if type(illusts1) is dict and illusts1 is not None:
                for illust in illusts1.keys():
                    illusts.append(illust)
            elif len(illusts) < 1:
                pass
            else:
                raise Exception("[ERROR]获取插画失败!")
            # 漫画
            manga = []
            manga1 = body.get("manga")
            if type(manga1) is dict and manga1 is not None:
                for manga2 in manga1.keys():
                    manga.append(manga2)
            elif len(manga) < 1:
                manga = []
            else:
                raise Exception("[ERROR]获取漫画失败!")
            # 漫画系列
            mangaSeries = str(re.findall(
                "'mangaSeries'.*?}]", str(ids_json), re.S))
            # 小说系列
            novelSeries = str(re.findall(
                "'novelSeries'.*?}]", str(ids_json), re.S))
            # 小说
            novels = str(re.findall("'novels'.*?}]", str(ids_json), re.S))

            # reeturn ids
            if len(illusts) != 0 and self.download_type.get("getillusts"):
                Ids["illusts"] = illusts
            if len(manga) != 0 and self.download_type.get("getmanga"):
                Ids["manga"] = manga
            if len(mangaSeries) != 0 and self.download_type.get("getmangaSeries"):
                mangaSeries_1 = str(re.findall("'id':.*?,", mangaSeries, re.S))
                mangaSeries_ids = re.findall("[0-9]+", mangaSeries_1, re.S)
                Ids["mangaSeries"] = mangaSeries_ids
            if len(novelSeries) != 0 and self.download_type.get("getnovelSeries"):
                novelSeries_1 = str(re.findall("'id':.*?,", novelSeries, re.S))
                novelSeries_ids = re.findall("[0-9]+", novelSeries_1, re.S)
                Ids["novelSeries"] = novelSeries_ids
            if len(novels) != 0 and self.download_type.get("getnovels"):
                novels_1 = str(re.findall("'id':.*?,", novels, re.S))
                novels_ids = re.findall("[0-9]+", novels_1, re.S)
                Ids["novels"] = novels_ids
            # 等待，防止封IP
            time.sleep(0.5)
        return Ids

    async def bound_get_id_async(self, session: aiohttp.ClientSession, tag=None, user=None) -> dict:
        async with self.semaphore:
            future = await self.get_id_async(session, tag, user)
            return future

    async def get_id_async(self, session: aiohttp.ClientSession, tag=None, user=None) -> dict:
        """获取作者所有作品的id"""
        if not self.event.is_set():
            return
        Ids = {}
        if tag is not None:
            pass

            # All_Ids['tag'] = Ids
            # 等待，防止封IP

        elif user is not None:
            uid, name = user
            self.logger.info("获取%s(uid:%s)的作品信息......" % (name, uid))
            self.headers.update(
                {"referer": "https://www.pixiv.net/users/{}".format(uid)})
            xhr_url = (
                "https://www.pixiv.net/ajax/user/{}/profile/all?lang=zh&version={}".format(
                    uid, version)
            )
            error_count = 0
            while 1:
                ids_json = 0
                try:
                    res = await session.get(
                        xhr_url,
                        headers=self.headers,
                    )
                    ids_json = await res.json()
                except asyncio.exceptions.TimeoutError:
                    self.logger.warning("连接超时!  请检查你的网络!")
                    return None
                except Exception:
                    print(await res.text())
                    self.logger.error("获取ID失败")
                    error_count += 1
                    if error_count == 4:
                        self.logger.info("自动重试失败!")
                        return None
                    self.logger.info("自动重试---%d/3" % error_count)
                finally:
                    if ids_json is not None:
                        if error_count:
                            self.logger.info("自动重试成功!")
                        break

            body = ids_json.get("body")
            if type(body) is not dict:
                # raise Exception('[ERROR]获取ID失败!',body)
                # print("[ERROR]获取ID失败!")
                # print(ids_json)
                self.logger.error("获取ID失败!\nIds:%s" % str(ids_json))
                return None
            # 插图
            illusts = []
            illusts1 = body.get("illusts")
            if type(illusts1) is dict and illusts1 is not None:
                for illust in illusts1.keys():
                    illusts.append(illust)
            elif len(illusts) < 1:
                pass
            else:
                raise Exception("[ERROR]获取插画失败!")
            # 漫画
            manga = []
            manga1 = body.get("manga")
            if type(manga1) is dict and manga1 is not None:
                for manga2 in manga1.keys():
                    manga.append(manga2)
            elif len(manga) < 1:
                manga = []
            else:
                raise Exception("[ERROR]获取漫画失败!")
            # 漫画系列
            mangaSeries = str(re.findall(
                "'mangaSeries'.*?}]", str(ids_json), re.S))
            # 小说系列
            novelSeries = str(re.findall(
                "'novelSeries'.*?}]", str(ids_json), re.S))
            # 小说
            novels = str(re.findall("'novels'.*?}]", str(ids_json), re.S))

            # reeturn ids
            if len(illusts) != 0 and self.download_type.get("getillusts"):
                Ids["illusts"] = illusts
            if len(manga) != 0 and self.download_type.get("getmanga"):
                Ids["manga"] = manga
            if len(mangaSeries) != 0 and self.download_type.get("getmangaSeries"):
                mangaSeries_1 = str(re.findall("'id':.*?,", mangaSeries, re.S))
                mangaSeries_ids = re.findall("[0-9]+", mangaSeries_1, re.S)
                Ids["mangaSeries"] = mangaSeries_ids
            if len(novelSeries) != 0 and self.download_type.get("getnovelSeries"):
                novelSeries_1 = str(re.findall("'id':.*?,", novelSeries, re.S))
                novelSeries_ids = re.findall("[0-9]+", novelSeries_1, re.S)
                Ids["novelSeries"] = novelSeries_ids
            if len(novels) != 0 and self.download_type.get("getnovels"):
                novels_1 = str(re.findall("'id':.*?,", novels, re.S))
                novels_ids = re.findall("[0-9]+", novels_1, re.S)
                Ids["novels"] = novels_ids
        return (name, Ids)

    def get_info(self, url, id) -> dict:
        """
        获取图片详情信息
        illust_info:如果要爬其他类型的作品时不一样!
        """
        fail = False
        try:
            work_html = requests.get(
                url=url,
                headers=self.headers,
                cookies=self.cookies,
                proxies=proxie,
                verify=False,
            ).text
        except Exception:
            fail = True
        if (
            (len(work_html) <= 100)
            or re.search("error-message", work_html, re.S)
            or fail
        ):
            self.logger.warning("获取html失败!")
            for a in range(1, 4):
                self.logger.info("自动重试---%d/3" % a)
                time.sleep(5)
                work_html = requests.get(
                    url=url,
                    headers=self.headers,
                    cookies=self.cookies,
                    proxies=proxie,
                    verify=False,
                ).text
                if len(work_html) >= 100:
                    self.logger.info("自动重试成功!")
                    break
                else:
                    self.logger.info("自动重试失败!")
        try:
            info_1 = re.search(
                r'\<meta.name="preload-data".*?\>', work_html, re.S
            ).group()
        except Exception:
            # print("获取html失败!")
            # print(work_html+"\n\n")
            # print(url)
            self.logger.error("获取html失败!\nUrl:%s" % url)
            return
        info_json = json.loads(
            re.search(r"(?<=content=').*?(?=')", info_1, re.S).group()
        )
        illust_info = info_json.get("illust").get(id)
        # print(illust_info)
        # work_type = illust_info.get("illustType")
        title1 = illust_info.get("illustTitle")
        title = illust_info.get("title")
        if title != title1:
            raise Exception("解析方式错误---title")
        description1 = illust_info.get("illustComment")
        description_1 = illust_info.get("description")
        if description1 != description_1:
            raise Exception("解析方式错误---description")
        # handle html escape characters with html
        description = html.unescape(description_1)
        # if don't unescape completely, use this:
        if re.search(r"&#\d", description, re.S):
            description = html.unescape(description)
        # remove <br> and <a>
        # description = re.sub(r"<br.*?/>", "\n", description)
        # description = re.sub(r'<a href=.*?target="_blank">', "", description)
        # description = re.sub(r"</a>", "", description)
        # print(description)

        tags1 = illust_info.get("tags").get("tags")
        local_var_tags = {}
        for text in tags1:
            tag = text.get("tag")
            translation = text.get("translation")
            if translation:
                translation = translation.get("en")
            local_var_tags.update({tag: translation})
        # all_url = re.search('(?<=urls":{).*?(?=})',info_2,re.S).group()
        userId = illust_info.get("userId")
        username = illust_info.get("userName")
        # userAccount = illust_info.get("userAccount")
        # 解析原图链接
        original_urls = []
        # 图片保存路径
        relative_path = []
        xhr_url = (
            "https://www.pixiv.net/ajax/illust/{}/pages?lang=zh&version={}".format(
                id, version)
        )
        self.headers.update(
            {"referer": "https://www.pixiv.net/artworks/%s" % id})
        try:
            # =======================================================
            # 获取xhr返回的json
            img_json = requests.get(
                xhr_url,
                headers=self.headers,
                cookies=self.cookies,
                verify=False,
                proxies=proxie,
            ).json()
        except Exception:
            self.logger.error("获取作品信息失败\nID:%s" % id)
            for a in range(1, 4):
                self.logger.info("自动重试---%d/3" % a)
                time.sleep(5)
                try:
                    img_json = requests.get(
                        xhr_url,
                        headers=self.headers,
                        cookies=self.cookies,
                        verify=False,
                        proxies=proxie,
                    ).json()
                    if img_json is not None:
                        self.logger.info("自动重试成功!")
                        break
                except Exception:
                    self.logger.info("自动重试失败!")
        body = img_json.get("body")
        for one in body:
            urls = one.get("urls")
            original = urls.get("original")
            # 检测是否是动图
            if re.search(r"_ugoira0", original):
                original = re.sub(r"_ugoira0.*", "_ug", original)
            name = re.search(r"[0-9]+\_.*", str(original)).group()
            if re.search(r"_ug", name):
                name = re.sub("_ug", ".gif", name)
            relative_path.append("picture/" + userId + "/" + name)
            original_urls.append(original)
        info = {
            "id": int(id),
            "title": title,
            "description": description,
            "tags": local_var_tags,
            "original_url": original_urls,
            "userId": userId,
            "username": username,
            "relative_path": relative_path,
        }

        for key in info:
            if info[key] is None and key != "description":
                raise Exception("解析方式错误---%s" % info)
        return info

    async def bound_get_info_async(self, url: str, id: str, session: aiohttp.ClientSession):
        async with self.semaphore:
            future = await self.get_info_async(url, id, session)
            return future

    async def get_info_async(self, url: str, id: str, session: aiohttp.ClientSession) -> dict:
        """
        获取图片详情信息
        illust_info:如果要爬其他类型的作品时不一样!
        """
        if not self.event.is_set():
            return
        self.logger.info("获取作品信息......ID:%s" % id)
        fail = False
        error_count = 0
        while 1:
            try:
                res = await session.get(
                    url=url,
                    headers=self.headers,
                )
                work_html = await res.text()
            except asyncio.exceptions.TimeoutError:
                self.logger.warning("连接超时!  请检查你的网络!")
                return None
            except Exception:
                fail = True
            if (
                (len(work_html) <= 100)
                or re.search("error-message", work_html, re.S)
                or fail
            ):
                self.logger.warning("获取html失败!")
                error_count += 1
                if error_count == 4:
                    self.logger.info("自动重试失败!")
                    return None
                self.logger.info("自动重试---%d/3" % error_count)
            else:
                if error_count:
                    self.logger.info("自动重试成功!")
                break
        try:
            info_1 = re.search(
                r'\<meta.name="preload-data".*?\>', work_html, re.S
            ).group()
        except Exception:
            # print("获取html失败!")
            # print(work_html+"\n\n")
            # print(url)
            self.logger.error("获取html失败!\nUrl:%s" % url)
            return
        info_json = json.loads(
            re.search(r"(?<=content=').*?(?=')", info_1, re.S).group()
        )
        illust_info = info_json.get("illust").get(id)
        # print(illust_info)
        # work_type = illust_info.get("illustType")
        title1 = illust_info.get("illustTitle")
        title = illust_info.get("title")
        if title != title1:
            raise Exception("解析方式错误---title")
        description1 = illust_info.get("illustComment")
        description = illust_info.get("description")
        if description1 != description:
            raise Exception("解析方式错误---description")
        tags1 = illust_info.get("tags").get("tags")
        local_var_tags = {}
        for text in tags1:
            tag = text.get("tag")
            translation = text.get("translation")
            if translation:
                translation = translation.get("en")
            local_var_tags.update({tag: translation})
        # all_url = re.search('(?<=urls":{).*?(?=})',info_2,re.S).group()
        userId = illust_info.get("userId")
        username = illust_info.get("userName")
        # userAccount = illust_info.get("userAccount")
        # 解析原图链接
        original_urls = []
        # 图片保存路径
        relative_path = []
        xhr_url = (
            "https://www.pixiv.net/ajax/illust/{}/pages?lang=zh&version={}".format(
                id, version)
        )
        self.headers.update(
            {"referer": "https://www.pixiv.net/artworks/%s" % id})
        error_count = 0
        while 1:
            img_json = 0
            try:
                # 获取xhr返回的json
                res = await session.get(
                    xhr_url,
                    headers=self.headers,
                )
                img_json = await res.json()
            except asyncio.exceptions.TimeoutError:
                self.logger.warning("连接超时!  请检查你的网络!")
                return None
            except Exception:
                img_json = None
                self.logger.error("获取作品信息失败\nID:%s" % id)
                error_count += 1
                if error_count == 4:
                    self.logger.info("自动重试失败!")
                    return None
                self.logger.info("自动重试---%d/3" % error_count)
            finally:
                if isinstance(img_json, dict):
                    if error_count:
                        self.logger.info("自动重试成功!")
                break
        body = img_json.get("body")
        for one in body:
            urls = one.get("urls")
            original = urls.get("original")
            # 检测是否是动图
            if re.search(r"_ugoira0", original):
                original = re.sub(r"_ugoira0.*", "_ug", original)
            name = re.search(r"[0-9]+\_.*", str(original)).group()
            if re.search(r"_ug", name):
                name = re.sub("_ug", ".gif", name)
            relative_path.append("picture/" + userId + "/" + name)
            original_urls.append(original)
        info = {
            "id": int(id),
            "title": title,
            "description": description,
            "tags": local_var_tags,
            "original_url": original_urls,
            "userId": userId,
            "username": username,
            "relative_path": relative_path,
        }

        for key in info:
            if info[key] is None and key != "description":
                raise Exception("解析方式错误---%s" % info)

        return info

    def record_in_tags(self, tags):
        self.tags_collection = self.db["All Tags"]
        for name, translate in tags.items():
            earlier = self.tags_collection.find_one({"name": name})
            if earlier:
                earlier_translate = earlier.get("translate")
                if earlier_translate is None and translate:
                    self.tags_collection.update_one(
                        {"name": name}, {"$set": {"translate": translate}}
                    )
                elif earlier_translate and translate:
                    if translate in earlier_translate.split("||"):
                        pass
                    else:
                        self.tags_collection.update_one(
                            {"name": name},
                            {
                                "$set": {
                                    "translate": earlier_translate + "||" + translate
                                }
                            },
                        )
                works_number = earlier.get("works_number") + 1
                b = self.tags_collection.update_one(
                    {"name": name}, {"$set": {"works_number": works_number}}
                )
                if not b:
                    raise Exception(b)
            else:
                self.tags_collection.insert_one(
                    {"name": name, "works_number": 1, "translate": translate}
                )

    async def record_in_tags_async(self, tags):
        self.tags_collection = self.db["All Tags"]
        for name, translate in tags.items():
            earlier = await self.tags_collection.find_one({"name": name})
            if earlier:
                earlier_translate = earlier.get("translate")
                if earlier_translate is None and translate:
                    await self.tags_collection.update_one(
                        {"name": name}, {"$set": {"translate": translate}}
                    )
                elif earlier_translate and translate:
                    if translate in earlier_translate.split("||"):
                        pass
                    else:
                        await self.tags_collection.update_one(
                            {"name": name},
                            {
                                "$set": {
                                    "translate": earlier_translate + "||" + translate
                                }
                            },
                        )
                works_number = earlier.get("works_number") + 1
                b = await self.tags_collection.update_one(
                    {"name": name}, {"$set": {"works_number": works_number}}
                )
                if not b:
                    raise Exception(b)
            else:
                await self.tags_collection.insert_one(
                    {"name": name, "works_number": 1, "translate": translate}
                )

    def record_info_mongodb(self, name, ids, collection) -> None:
        """将图片详情信息保存在mongodb中"""
        exists = collection.find(
            {"id": {"$exists": True}}, {"_id": 0, "id": 1})
        exists_id = [id.get("id") for id in exists]
        for key in list(ids.keys()):
            # 插图
            if key == "illusts" and self.download_type.get("getillusts"):
                _ids = ids.get(key)
                ids_count = len(_ids)
                for a in range(ids_count):
                    id = _ids.pop()
                    if int(id) in exists_id:
                        # print(find)
                        # print('已存在,跳过')
                        self.progress_signal.emit(
                            [0, ("爬取%s的作品信息......" % name, int(100 * a / ids_count))])
                        continue
                    self.logger.info("获取作品信息......ID:%s" % id)
                    info = {"type": key}
                    url = "https://www.pixiv.net/artworks/" + id
                    info.update(self.get_info(url=url, id=id))
                    res = collection.insert_one(info)
                    if res:
                        self.record_in_tags(info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    if not self.event.is_set():
                        return
                    self.progress_signal.emit(
                        [0, ("爬取%s(uid:%s)的作品信息......", int(100 * a / ids_count))])
            # 漫画
            elif key == "manga" and self.download_type.get("getmanga"):
                _ids = ids.get(key)
                ids_count = len(_ids)
                for a in range(ids_count):
                    id = _ids.pop()
                    if int(id) in exists_id:
                        # print('已存在,跳过')
                        continue
                    self.logger.info("获取作品链接...ID:%s" % id)
                    info = {"type": key}
                    url = "https://www.pixiv.net/artworks/" + id
                    info.update(self.get_info(url=url, id=id))
                    res = collection.insert_one(info)
                    if res:
                        self.record_in_tags(info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    if not self.event.is_set():
                        return
                    self.progress_signal.emit(
                        [0, ("爬取%s(uid:%s)的作品信息......", int(100 * a / ids_count))])
            # 漫画系列
            elif key == "mangaSeries" and self.download_type.get("getmangaSeries"):
                pass
            # 小说系列
            elif key == "novelSeries" and self.download_type.get("getnovelSeries"):
                pass
            # 小说
            elif key == "novels" and self.download_type.get("getnovels"):
                pass
        # self.progress_signal.emit([0, ("No Process", 100)])

    async def record_info_mongodb_async(self, ids: dict, session: aiohttp.ClientSession, collection) -> None:
        """将图片详情信息保存在mongodb中"""
        exists = collection.find(
            {"id": {"$exists": True}}, {"_id": 0, "id": 1})
        exists_id = [id.get("id") async for id in exists]
        # exists_id = [id.get("id") for id in exists]
        for key in list(ids.keys()):
            # 插图
            if key == "illusts" and self.download_type.get("getillusts"):
                _ids = ids.get(key)
                task_list = []
                for _id in _ids:
                    if int(_id) in exists_id:
                        # print(find)
                        # print('已存在,跳过')
                        continue
                    url = "https://www.pixiv.net/artworks/" + _id
                    _info = self.bound_get_info_async(
                        url=url, id=_id, session=session)
                    task = asyncio.create_task(_info)
                    task_list.append(task)
                futurelist = await asyncio.gather(*task_list)
                for future in futurelist:
                    info = {"type": key}
                    info.update(future)
                    res = await collection.insert_one(info)
                    if res:
                        await self.record_in_tags_async(info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    # print(info)
                if not self.event.is_set():
                    return
            # 漫画
            elif key == "manga" and self.download_type.get("getmanga"):
                _ids = ids.get(key)
                for _id in _ids:
                    if int(_id) in exists_id:
                        # print(find)
                        # print('已存在,跳过')
                        continue
                    url = "https://www.pixiv.net/artworks/" + _id
                    _info = self.bound_get_info_async(
                        url=url, id=_id, session=session)
                    task = asyncio.create_task(_info)
                    task_list.append(task)
                futurelist = await asyncio.gather(*task_list)
                for future in futurelist:
                    info = {"type": key}
                    info.update(future)
                    res = await collection.insert_one(info)
                    if res:
                        await self.record_in_tags_async(info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    # print(info)
                    if not self.event.is_set():
                        return
            # 漫画系列
            elif key == "mangaSeries" and self.download_type.get("getmangaSeries"):
                pass
            # 小说系列
            elif key == "novelSeries" and self.download_type.get("getnovelSeries"):
                pass
            # 小说
            elif key == "novels" and self.download_type.get("getnovels"):
                pass

    def mongoDB_auto_backup(self):
        self.logger.info("开始自动备份,请勿关闭程序!!!")
        names = self.db.list_collection_names()
        now = 1
        all = len(names)
        for name in names:
            collection = self.db[name]
            a = collection.find({"id": {"$exists": True}}, {"_id": 0})
            for docs in a:
                if len(docs) >= 9:
                    b = self.backup_collection.find_one({"id": docs.get("id")})
                    if b:
                        continue
                    else:
                        self.backup_collection.insert_one(docs)
            self.progress_signal.emit([("备份数据库......", int(100 * now / all))])
            now += 1
        self.logger.info("自动备份完成!")
        return True

    async def mongoDB_auto_backup_async(self):
        self.logger.info("开始自动备份,请勿关闭程序!!!")
        names = await self.db.list_collection_names()
        for name in names:
            collection = self.db[name]
            a = collection.find({"id": {"$exists": True}}, {"_id": 0})
            async for docs in a:
                if len(docs) >= 9:
                    b = self.backup_collection.find_one({"id": docs.get("id")})
                    if b:
                        continue
                    else:
                        await self.backup_collection.insert_one(docs)
        self.logger.info("自动备份完成!")
        return True

    def stop_getting(self):
        self.event.clear()
        time.sleep(0.5)
        self.logger.info("停止获取作者的作品信息")


class Downloader:
    """
    下载图片(下载小说?->future)
    """

    def __init__(
        self, host_path, cookies, download_type, download_number, backup_collection, logger, progress_signal
    ) -> None:
        self.cookies = cookies
        self.host_path = host_path
        self.download_type = download_type
        self.backup_collection = backup_collection
        self.logger = logger
        self.progress_signal = progress_signal
        self.headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
            "referer": "https://www.pixiv.net/"}
        self.pool = ThreadPoolExecutor(max_workers=download_number)
        self.event = threading.Event()
        self.event.set()

    def start_work_download(self, id):
        """
        从图片url下载
        """
        print("开始下载")
        tasks = []
        infogetter = InfoGetter(
            self.cookies, self.download_type, None, self.backup_collection
        )
        infos = infogetter.get_info(
            url="https://www.pixiv.net/artworks/" + id, id=id)
        del infogetter
        urls = infos.get("original_url")
        relative_path = []
        # 检测下载路径是否存在,不存在则创建
        if os.path.isdir(self.host_path + "works/" + id + "/") is False:
            os.makedirs(self.host_path + "works/" + id + "/")

        for a in range(len(urls)):
            url = urls[a]
            name = re.search(r"[0-9]+\_.*", url).group()
            path = self.host_path + "works/" + id + "/" + name
            relative_path.append("works/" + id + "/" + name)
            # 检测是否已下载
            if not os.path.isfile(path=path):
                info = [id, url, path]
                tasks.append(self.pool.submit(self.download_image, info))

        infos.update({"relative_path": relative_path})
        with open(
            "{}works/{}/info.json".format(self.host_path, id), "w", encoding="utf-8"
        ) as f:
            json.dump(infos, f, ensure_ascii=False, indent=4)

        for future in as_completed(tasks):
            if not self.event.is_set():
                return
            future.result()
        self.pool.shutdown()
        print("下载完成")

    def start_tag_download(self):
        """
        从pixiv获取含标签的图片下载
        """

    def start_user_download(self):
        """
        从mongodb中获取图片url并放进线程池
        """

    def start_following_download(self):
        """
        从mongodb中获取图片url并放进线程池
        """
        self.logger.info("开始下载\n由于需要读取数据库信息并检测是否下载,所以可能等待较长时间")
        tasks = []
        for doc in self.backup_collection.find({"id": {"$exists": True}}):
            if not self.event.is_set():
                return
            tasks.clear()
            if doc.get("failcode"):
                continue
            if not self.download_type.get("get" + doc.get("type")):
                self.logger.warning("作品%s不在下载类型%s中" %
                                    (doc.get("id"), "get" + doc.get("type")))
                # print(doc)
            id = doc.get("id")
            urls = doc.get("original_url")
            uid = doc.get("userId")
            paths = doc.get("relative_path")
            if len(paths) < 1:
                self.logger.warning("数据错误:\n%s" % str(doc))
                continue
            for a in range(len(urls)):
                try:
                    url = urls[a]
                    path = self.host_path + paths[a]
                except Exception:
                    print(doc)
                    continue

                # 检测下载路径是否存在,不存在则创建
                if os.path.isdir(self.host_path + "/picture/" + uid + "/") is False:
                    os.makedirs(self.host_path + "/picture/" + uid + "/")
                # 检测是否已下载
                if not os.path.isfile(path=path):
                    info = [id, url, path]
                    tasks.append(self.pool.submit(self.download_image, info))

            for future in as_completed(tasks):
                if not self.event.is_set():
                    return
                future.result()
        self.pool.shutdown()
        self.logger.info("下载完成")

    def invalid_image_recorder(self, id, failcode):
        doc = self.backup_collection.find_one_and_update(
            {"id": id}, {"$set": {"failcode": failcode}}
        )
        if not doc:
            self.logger.error(
                "error in record invaild image:" + id + "\n" + doc)

    def stream_download(self, request_info, path):
        """
        流式接收数据并写入文件
        """
        url, headers = request_info
        try:
            response = requests.get(
                url,
                headers=headers,
                cookies=self.cookies,
                verify=False,
                proxies=proxie,
                stream=True,
            )
        except Exception:
            self.logger.warning("下载失败!")
            for a in range(1, 4):
                self.logger.info("自动重试---%d/3" % a)
                time.sleep(3)
                try:
                    response = requests.get(
                        url,
                        headers=headers,
                        cookies=self.cookies,
                        verify=False,
                        proxies=proxie,
                        stream=True,
                    )
                    if response.status_code != 200:
                        self.logger.warning("下载失败!---响应状态码:%d" %
                                            response.status_code)
                    f = open(path, "wb")
                    for chunk in response.iter_content(1024):
                        if not self.event.is_set():
                            f.close()
                            os.remove(path)
                            return
                        f.write(chunk)
                        f.flush()
                    f.close()
                except Exception:
                    self.logger.info("自动重试失败!")
                    return 1
                    # 错误记录，但感觉没什么用
                    # if a == 3:self.failure_recoder_mongo(id)
        if response.status_code != 200:
            self.logger.warning("下载失败!---响应状态码:%d" % response.status_code)
            return response.status_code
        f = open(path, "wb")
        for chunk in response.iter_content(1024):
            if not self.event.is_set():
                f.close()
                os.remove(path)
                return
            f.write(chunk)
            f.flush()
        f.close()

    async def stream_download_async(self, session: aiohttp.ClientSession, request_info, path):
        """
        流式接收数据并写入文件
        """
        url, headers = request_info
        while 1:
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    cookies=self.cookies,
                    stream=True,
                )
            except Exception:
                self.logger.warning("下载失败!")
                for a in range(1, 4):
                    self.logger.info("自动重试---%d/3" % a)
                    time.sleep(3)
                    try:
                        response = requests.get(
                            url,
                            headers=headers,
                            cookies=self.cookies,
                            verify=False,
                            proxies=proxie,
                            stream=True,
                        )
                        if response.status_code != 200:
                            self.logger.warning("下载失败!---响应状态码:%d" %
                                                response.status_code)
                        f = open(path, "wb")
                        for chunk in response.iter_content(1024):
                            if not self.event.is_set():
                                f.close()
                                os.remove(path)
                                return
                            f.write(chunk)
                            f.flush()
                        f.close()
                    except Exception:
                        self.logger.info("自动重试失败!")
                        return 1
                        # 错误记录，但感觉没什么用
                        # if a == 3:self.failure_recoder_mongo(id)
        if response.status_code != 200:
            self.logger.warning("下载失败!---响应状态码:%d" % response.status_code)
            return response.status_code
        f = open(path, "wb")
        for chunk in response.iter_content(1024):
            if not self.event.is_set():
                f.close()
                os.remove(path)
                return
            f.write(chunk)
            f.flush()
        f.close()

    def download_image(self, info):
        """从队列中获取数据并下载图片"""
        if not self.event.is_set():
            return
        start_time = time.time()  # 程序开始时间
        # print('获取数据%s'%(info))
        id = str(info[0])
        url = info[1]
        path = info[2]
        if re.search("ug", url, re.S) is not None:
            info = re.search("img/.*", url).group()
            save_name = id + ".zip"
            image_dir = id + "/"
            zip_url = "https://i.pximg.net/img-zip-ugoira/" + info + "oira1920x1080.zip"
            self.logger.info("下载动图ID:%s" % id)
            failcode = self.stream_download((zip_url, self.headers), save_name)
            if failcode:
                if failcode != 1:
                    self.invalid_image_recorder(int(id), failcode)
                    return
                else:
                    self.logger.error("下载图片%s失败" % id)
                    return
            with zipfile.ZipFile(save_name, "r") as f:
                for file in f.namelist():
                    f.extract(file, image_dir)
            # 删除临时zip文件
            os.remove(save_name)
            # 获取图片路径列表
            image_list = glob.glob(image_dir + "*.jpg")
            # 创建GIF动图对象
            gif_images = [Image.open(image_path) for image_path in image_list]
            # 保存为GIF动图
            with gif_images[0] as first_image:
                first_image.save(
                    path,
                    save_all=True,
                    append_images=gif_images[1:],
                    optimize=False,
                    duration=50,
                    loop=0,
                )
            # 删除解压图片文件夹
            for file_name in os.listdir(image_dir):
                tf = os.path.join(image_dir, file_name)
                os.remove(tf)
            os.rmdir(image_dir)
        else:
            img_url = "https://www.pixiv.net/artworks/" + id
            self.headers.update({"referer": img_url})
            self.logger.info("下载图片:ID:%s" % id)
            failcode = self.stream_download((url, self.headers), path)
            if failcode:
                if failcode != 1:
                    self.invalid_image_recorder(int(id), failcode)
                    return
                else:
                    self.logger.error("下载图片%s失败" % id)
                    return
        if not self.event.is_set():
            return
        end_time = time.time()  # 程序结束时间
        run_time = end_time - start_time  # 程序的运行时间，单位为秒
        if os.path.exists(path):
            self.logger.info(
                "下载图片{}完成,耗时:{},保存至:{}".format(id, run_time, path))
        else:
            self.logger.error("图片保存失败")

    def pause_downloading(self):
        pass

    def stop_downloading(self):
        self.event.clear()
        time.sleep(0.5)
        self.pool.shutdown(wait=True, cancel_futures=True)
        self.logger.info("停止下载")
        return


class Tools:
    def __init__(self) -> None:
        pass

    def compare_datetime(lasttime: str, newtime: str) -> bool:
        time1 = [lasttime[0:4], lasttime[4:6], lasttime[6:8]]
        time2 = [newtime[0:4], newtime[4:6], newtime[6:8]]
        # print(time1,time2)
        if time2[0] > time1[0]:
            return True
        elif time2[0] == time1[0]:
            if time2[1] > time1[1]:
                return True
            elif time2[1] == time1[1]:
                return time2[2] > time1[2]
        return False

    def search(collection, search_info, page_number):
        all_founded = []
        work_number = 0

        if re.findall(r"\+", search_info):
            and_search = []
            for one_search in search_info.split("+"):
                if re.search(r"\d{4,}", one_search):
                    and_search.append({"userId": one_search})
                else:
                    and_search.append(
                        {"tags." + one_search: {"$exists": "true"}})
            results = collection.find({"$and": and_search}).sort("id", -1)
            # self.results = collection.find({"$and":and_search})
            # self.work_number = collection.find({"$and":and_search})

        elif re.findall(r"\,", search_info):
            or_search = []
            for one_search in search_info.split(","):
                if re.search(r"\d{4,}", one_search):
                    or_search.append({"userId": one_search})
                else:
                    or_search.append(
                        {"tags." + one_search: {"$exists": "true"}})
                results = collection.find({"$or": or_search}).sort("id", -1)

        else:
            one_search = {}
            if re.search(r"\d{4,}", search_info):
                one_search.update({"userId": search_info})
            else:
                one_search.update({"tags." + search_info: {"$exists": "true"}})
            results = collection.find(one_search).sort("id", -1)

        for row in results:
            all_founded.append(row)
            work_number += 1
            # print(row.get("id"))
        total_page = (work_number - 1) // (page_number) + 1
        return all_founded, total_page

    def analyze_cookie(oringal_cookies):
        cookies = {}
        for cookie in oringal_cookies.split(";"):
            key, value = cookie.split("=", 1)
            cookies[key] = value
        return cookies


if __name__ == "__main__":
    a = "{'afaf':'a5af','fw':8464}"
    b = "_gcl_au=1.1.1140122344.1692758372; login_ever=yes; c_type=24;"
    print(eval(a))
    print(eval(b))
