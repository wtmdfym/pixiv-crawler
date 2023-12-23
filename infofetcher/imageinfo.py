# -*-coding:utf-8-*-
from parsel import Selector
import httpx
import aiohttp
import asyncio
import requests
import re
import json
import html
import time

import threading

import http.cookies
http.cookies._is_legal_key = lambda _: True


class InfoFetcher:
    """
    Get information about works

    Use asyncio and aiohttp

    Attributes:
        __version: Parameters in the Pixiv request link (usefulness unknown)
        __proxies: Proxy to use aiohttp to send HTTP requests (optional)
        __event: The stop event
        db: The database connection of MongoDB(async)
        cookies:The cookies when a request is sent to pixiv
        download_type: The type of work to be downloaded
        backup_collection: A collection of backup of info(async)
        logger: The instantiated object of logging.Logger
        progress_signal: The pyqtSignal of QProgressBar
        headers: The headers when sending a HTTP request to pixiv
        timeout: The timeout period for aiohttp requests
        semaphore: The concurrent semaphore of asyncio
    """
    __version = '54b602d334dbd7fa098ee5301611eda1776f6f39'
    __proxies = 'http://localhost:1111'
    __event = asyncio.Event()

    def __init__(self, cookies: str, download_type: dict, asyncdb, backup_collection, logger,
                 semaphore: int = None, progress_signal=None) -> None:
        self.db = asyncdb
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
        self.__event.set()

    async def start_get_info_async(self) -> bool | None:
        """
        Raises:
            Exception:
        """
        finish = await self.record_infos_async()
        if finish:
            success = await self.mongoDB_auto_backup_async()
            if success:
                return True
            else:
                return False
                # raise Exception("database backup error")

    async def record_infos_async(self) -> bool:

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
                if not self.__event.is_set():
                    return False
                for future in futurelist:
                    if future:
                        name, ids = future
                        # print(name)
                        if ids:
                            # print("ok")
                            await self.record_info_mongodb_async(ids=ids, session=session, collection=self.db[name])
                await session.close()
        self.logger.info("获取所有作者的作品信息完成")
        return True

    async def bound_get_id_async(self, session: aiohttp.ClientSession, tag=None, user=None) -> dict:
        async with self.semaphore:
            future = await self.get_id_async(session, tag, user)
            return future

    async def get_id_async(self, session: aiohttp.ClientSession, tag=None, user=None) -> dict:
        """获取作者所有作品的id"""
        if not self.__event.is_set():
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
                    uid, self.__version)
            )
            error_count = 0
            while 1:
                ids_json = 0
                try:
                    res = await session.get(
                        xhr_url,
                        headers=self.headers,
                        proxy=self.__proxies,
                    )
                    ids_json = await res.json()
                except asyncio.exceptions.TimeoutError:
                    self.logger.warning("连接超时!  请检查你的网络!")
                    error_count += 1
                    if error_count == 4:
                        self.logger.info("自动重试失败!")
                        return None
                    self.logger.info("自动重试---%d/3" % error_count)
                except Exception:
                    print(await res.text())
                    self.logger.error("获取ID失败")
                    error_count += 1
                    if error_count == 4:
                        self.logger.info("自动重试失败!")
                        return None
                    self.logger.info("自动重试---%d/3" % error_count)
                finally:
                    if ids_json is not None and ids_json != 0:
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

    async def bound_get_info_async(self, url: str, id: str, session: aiohttp.ClientSession) -> dict:
        async with self.semaphore:
            future = await self.get_info_async(url, id, session)
            return future

    async def get_info_async(self, url: str, id: str, session: aiohttp.ClientSession) -> dict:
        """
        Get detailed information about a work
        TODO illust_info:It's not the same if you want to climb other types of works!

        Args:
            url(str): Request link
            id(str): The ID of the work
            session(aiohttp.ClientSession): Connection session with pixiv

        Returns:

            A dictionary of work information. Include the ID, title, description,
            tags, download link of the original image (if it is an image), author ID,
            author's name, and relative storage path. For example:

            {"id": 100774433,
                "title": "夏生まれ",
                "description": "らむねちゃん応援してます(๑╹ᆺ╹)",
                "tags": {
                    "バーチャルYouTuber": "虚拟主播",
                    "ぶいすぽっ!": "Virtual eSports Project",
                    "白波らむね": "Shiranami Ramune",
                    "可愛い": "可爱",
                    "夏": "夏天",
                    "海": "sea",
                    "女の子": "女孩子",
                    "青髪": None
                },
                "original_url": [
                    "https://i.pximg.net/img-original/img/2022/08/26/19/00/13/100774433_p0.png"
                ],
                "userId": "9155411",
                "username": "rucaco/るかこ",
                "relative_path": [
                    "picture/9155411/100774433_p0.png"
                ]
            }

        Raises:
            Exception: The parsing method is incorrect
        """
        if not self.__event.is_set():
            return
        self.logger.info("获取作品信息......ID:%s" % id)
        fail = False
        error_count = 0
        while 1:
            try:
                res = await session.get(
                    url=url,
                    headers=self.headers,
                    proxy=self.__proxies,
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
                id, self.__version)
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
                    proxy=self.__proxies,
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

    async def record_in_tags_async(self, id: int, tags) -> None:
        self.tags_collection = self.db["All Tags"]
        for name, translate in tags.items():
            earlier = await self.tags_collection.find_one({'name': name})
            if earlier:
                workids = earlier.get("workids")
                if workids:
                    workids.append(id)
                else:
                    workids = [id]
                works_count = earlier.get('works_count')+1
                earlier_translate = earlier.get('translate')
                if earlier_translate is None and translate:
                    await self.tags_collection.update_one(
                        {"name": name}, {"$set": {"translate": translate, 'works_count': works_count, "workids": workids}})
                elif earlier_translate and translate:
                    if translate in earlier_translate.split('||'):
                        await self.tags_collection.update_one(
                            {"name": name}, {"$set": {'works_count': works_count, "workids": workids}})
                    else:
                        await self.tags_collection.update_one({"name": name},
                                                              {"$set": {"translate": earlier_translate+'||'+translate,
                                                                        'works_count': works_count, "workids": workids}})
                elif (earlier_translate and translate) is None:
                    await self.tags_collection.update_one(
                        {"name": name}, {"$set": {'works_count': works_count, "workids": workids}})
                else:
                    print(id)
                    return
            else:
                await self.tags_collection.insert_one(
                    {'name': name, 'translate': translate, 'works_count': 1, "workids": [id]})

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
                        await self.record_in_tags_async(info.get("id"), info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    # print(info)
                if not self.__event.is_set():
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
                        await self.record_in_tags_async(info.get("id"), info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    # print(info)
                    if not self.__event.is_set():
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

    async def mongoDB_auto_backup_async(self) -> bool:
        self.logger.info("开始自动备份,请勿关闭程序!!!")
        names = await self.db.list_collection_names()
        for name in names:
            collection = self.db[name]
            # 可不用
            async with self.semaphore:
                async for docs in collection.find({"id": {"$exists": True}}, {"_id": 0}):
                    if not self.__event.is_set():
                        return False
                    if len(docs) >= 9:
                        b = await self.backup_collection.find_one({"id": docs.get("id")})
                        if b:
                            continue
                        else:
                            await self.backup_collection.insert_one(docs)
                            # print(c)
        self.logger.info("自动备份完成!")
        return True

    def set_proxies(self, proxies: tuple):
        return
        http_proxies = proxies[0]
        # https_proxies = proxies[1]
        self.__proxies = http_proxies

    def stop_getting(self):
        self.__event.clear()
        self.logger.info("停止获取作者的作品信息")


class InfoFetcherHttpx:
    """
    Get information about works

    Use asyncio and httpx

    Attributes:
        __version: Parameters in the Pixiv request link (usefulness unknown)
        __proxies: Proxy to use aiohttp to send HTTP requests (optional)
        __event: The stop event
        db: The database connection of MongoDB(async)
        cookies:The cookies when a request is sent to pixiv
        download_type: The type of work to be downloaded
        backup_collection: A collection of backup of info(async)
        logger: The instantiated object of logging.Logger
        progress_signal: The pyqtSignal of QProgressBar
        headers: The headers when sending a HTTP request to pixiv
        timeout: The timeout period for aiohttp requests
        semaphore: The concurrent semaphore of asyncio
    """
    __version = '54b602d334dbd7fa098ee5301611eda1776f6f39'
    __proxies = 'http://localhost:1111'
    __event = asyncio.Event()

    def __init__(self, cookies: str, download_type: dict, asyncdb, backup_collection, logger,
                 semaphore: int = None, progress_signal=None) -> None:
        self.db = asyncdb
        self.cookies = cookies
        self.download_type = download_type
        self.backup_collection = backup_collection
        self.logger = logger
        self.progress_signal = progress_signal
        self.headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
            "referer": "https://www.pixiv.net/"}
        self.timeout = httpx.Timeout(8.0, connect=10.0, read=25.0, pool=None)
        self.limits = httpx.Limits(
            max_keepalive_connections=semaphore, max_connections=semaphore)
        transport = httpx.AsyncHTTPTransport(
            proxy=self.__proxies, limits=self.limits, retries=2)
        self.client = httpx.AsyncClient(headers=self.headers, cookies=self.cookies,
                                        timeout=self.timeout, transport=transport)
        self.semaphore = asyncio.Semaphore(semaphore)
        self.__event.set()

    async def start_get_info(self) -> bool | None:
        """
        Raises:
            Exception:
        """
        finish = await self.record_infos()
        if finish:
            success = await self.mongoDB_auto_backup()
            if success:
                return True
            else:
                return False
                # raise Exception("database backup error")

    async def record_infos(self) -> bool:
        self.followings_collection = self.db["All Followings"]
        painters = self.followings_collection.find(
            {"userId": {"$exists": True}})
        task_list = []
        async for painter in painters:
            # for painter in painters:
            uid = painter.get("userId")
            name = painter.get("userName")
            ids = self.get_id(user=(uid, name))
            task = asyncio.create_task(ids)
            # task.add_done_callback(ids_callback)
            task_list.append(task)
            # break
        futurelist = await asyncio.gather(*task_list)
        if not self.__event.is_set():
            return False
        for future in futurelist:
            if future:
                name, ids = future
                # print(name)
                if ids:
                    # print("ok")
                    await self.record_info_mongodb(ids=ids, collection=self.db[name])
        await self.client.aclose()
        self.logger.info("获取所有作者的作品信息完成")
        return True

    async def get_id(self, tag=None, user=None) -> dict:
        async with self.semaphore:
            """获取作者所有作品的id"""
            if not self.__event.is_set():
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
                        uid, self.__version)
                )
                error_count = 0
                '''
                while True:
                    ids_json = {}
                    try:
                        res = await client.get(
                            xhr_url,
                            headers=self.headers,
                        )
                        ids_json = res.json()
                    except httpx.ConnectTimeout:
                        error_count += 1
                        self.logger.warning("连接超时!  请检查你的网络!")
                        self.logger.info("自动重试---%d/3" % error_count)
                    # except Exception:
                    #     error_count += 1
                    #     self.logger.error("获取ID失败")
                    #     self.logger.info("自动重试---%d/3" % error_count)
                    finally:
                        if error_count == 4:
                            self.logger.info("自动重试失败!")
                            return None
                        if ids_json:
                            if ids_json.get("error"):
                                self.logger.warning(
                                    "获取ID失败!    message:%s" % ids_json.get("message"))
                            if error_count:
                                self.logger.info("自动重试成功!")
                            break
                        else:
                            error_count += 1
                            self.logger.error("获取ID失败")
                            self.logger.info("自动重试---%d/3" % error_count)
                '''
                res = await self.client.get(xhr_url, headers=self.headers,)
                ids_json = res.json()
                if ids_json:
                    if ids_json.get("error"):
                        self.logger.warning(
                            "获取ID失败!    message:%s" % ids_json.get("message"))
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
                    mangaSeries_1 = str(re.findall(
                        "'id':.*?,", mangaSeries, re.S))
                    mangaSeries_ids = re.findall("[0-9]+", mangaSeries_1, re.S)
                    Ids["mangaSeries"] = mangaSeries_ids
                if len(novelSeries) != 0 and self.download_type.get("getnovelSeries"):
                    novelSeries_1 = str(re.findall(
                        "'id':.*?,", novelSeries, re.S))
                    novelSeries_ids = re.findall("[0-9]+", novelSeries_1, re.S)
                    Ids["novelSeries"] = novelSeries_ids
                if len(novels) != 0 and self.download_type.get("getnovels"):
                    novels_1 = str(re.findall("'id':.*?,", novels, re.S))
                    novels_ids = re.findall("[0-9]+", novels_1, re.S)
                    Ids["novels"] = novels_ids
            return (name, Ids)

    async def get_info(self, url: str, id: str) -> dict:
        """
        Get detailed information about a work
        TODO illust_info:It's not the same if you want to climb other types of works!

        Args:
            url(str): Request link
            id(str): The ID of the work
            session(aiohttp.ClientSession): Connection session with pixiv

        Returns:

            A dictionary of work information. Include the ID, title, description,
            tags, download link of the original image (if it is an image), author ID,
            author's name, and relative storage path. For example:

            {"id": 100774433,
                "title": "夏生まれ",
                "description": "らむねちゃん応援してます(๑╹ᆺ╹)",
                "tags": {
                    "バーチャルYouTuber": "虚拟主播",
                    "ぶいすぽっ!": "Virtual eSports Project",
                    "白波らむね": "Shiranami Ramune",
                    "可愛い": "可爱",
                    "夏": "夏天",
                    "海": "sea",
                    "女の子": "女孩子",
                    "青髪": None
                },
                "original_url": [
                    "https://i.pximg.net/img-original/img/2022/08/26/19/00/13/100774433_p0.png"
                ],
                "userId": "9155411",
                "username": "rucaco/るかこ",
                "relative_path": [
                    "picture/9155411/100774433_p0.png"
                ]
            }

        Raises:
            Exception: The parsing method is incorrect
        """
        async with self.semaphore:
            if not self.__event.is_set():
                return
            self.logger.info("获取作品信息......ID:%s" % id)
            error_count = 0
            while True:
                try:
                    response = await self.client.get(url=url, headers=self.headers)
                except httpx.ConnectError:
                    error_count += 1
                    # self.logger.warning("代理配置可能错误!  检查你的代理!")
                    continue
                except httpx.ConnectTimeout:
                    error_count += 1
                    # self.logger.warning("连接超时!  检查你的网络!")
                    continue
                # except Exception:
                #     fail = True
                work_html = response.text
                info = InfoParsel(work_html, self.client)
                info = await info.get_result()
                if info:
                    if error_count:
                        self.logger.info("自动重试成功!")
                    break
                else:
                    self.logger.warning("获取html失败!")
                    error_count += 1
                    if error_count == 4:
                        self.logger.info("自动重试失败!")
                        return None
                    self.logger.info("自动重试------%d/3" % error_count)
            return info

    async def record_in_tags(self, id: int, tags) -> None:
        self.tags_collection = self.db["All Tags"]
        for name, translate in tags.items():
            earlier = await self.tags_collection.find_one({'name': name})
            if earlier:
                workids = earlier.get("workids")
                if workids:
                    workids.append(id)
                else:
                    workids = [id]
                works_count = earlier.get('works_count')+1
                earlier_translate = earlier.get('translate')
                if earlier_translate is None and translate:
                    await self.tags_collection.update_one(
                        {"name": name}, {"$set": {"translate": translate, 'works_count': works_count, "workids": workids}})
                elif earlier_translate and translate:
                    if translate in earlier_translate.split('||'):
                        await self.tags_collection.update_one(
                            {"name": name}, {"$set": {'works_count': works_count, "workids": workids}})
                    else:
                        await self.tags_collection.update_one({"name": name},
                                                              {"$set": {"translate": earlier_translate+'||'+translate,
                                                                        'works_count': works_count, "workids": workids}})
                elif (earlier_translate and translate) is None:
                    await self.tags_collection.update_one(
                        {"name": name}, {"$set": {'works_count': works_count, "workids": workids}})
                else:
                    print(id)
                    return
            else:
                await self.tags_collection.insert_one(
                    {'name': name, 'translate': translate, 'works_count': 1, "workids": [id]})

    async def record_info_mongodb(self, ids: dict, collection) -> None:
        """将图片详情信息保存在mongodb中"""
        async with self.semaphore:
            exists = collection.find(
                {"id": {"$exists": True}}, {"_id": 0, "id": 1})
            exists_id = [id.get("id") async for id in exists]
            # exists_id = [id.get("id") for id in exists]
            for key in list(ids.keys()):
                _ids = ids.get(key)
                task_list = []
                for _id in _ids:
                    if int(_id) in exists_id:
                        # print(find)
                        # print('已存在,跳过')
                        continue
                    url = "https://www.pixiv.net/artworks/" + _id
                    _info = self.get_info(
                        url=url, id=_id)
                    task = asyncio.create_task(_info)
                    task_list.append(task)
                futurelist = await asyncio.gather(*task_list)
                for info in futurelist:
                    if not self.__event.is_set():
                        return
                    res = await collection.insert_one(info)
                    if res:
                        await self.record_in_tags(info.get("id"), info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    # print(info)
                if not self.__event.is_set():
                    return

            '''
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
                        await self.record_in_tags_async(info.get("id"), info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    # print(info)
                if not self.__event.is_set():
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
                        await self.record_in_tags_async(info.get("id"), info.get("tags"))
                    else:
                        self.logger.critical("记录tag失败")
                    # print(info)
                    if not self.__event.is_set():
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
            '''

    async def mongoDB_auto_backup(self) -> bool:
        self.logger.info("开始自动备份,请勿关闭程序!!!")
        names = await self.db.list_collection_names()
        for name in names:
            collection = self.db[name]
            # 可不用
            async with self.semaphore:
                async for docs in collection.find({"id": {"$exists": True}}, {"_id": 0}):
                    if not self.__event.is_set():
                        return False
                    if len(docs) >= 9:
                        b = await self.backup_collection.find_one({"id": docs.get("id")})
                        if b:
                            continue
                        else:
                            await self.backup_collection.insert_one(docs)
                            # print(c)
        self.logger.info("自动备份完成!")
        return True

    def set_proxies(self, proxies: tuple):
        return
        http_proxies = proxies[0]
        # https_proxies = proxies[1]
        self.__proxies = http_proxies

    def stop_getting(self):
        self.__event.clear()
        self.logger.info("停止获取作者的作品信息")


class InfoParsel:
    def __init__(self, work_html: str, client: httpx.AsyncClient) -> None:
        self.client = client
        selector = Selector(text=work_html)
        preload_datas = selector.xpath(
            '//meta[@id="meta-preload-data"]/@content').get()
        # or re.search("error-message", work_html, re.S)
        if not preload_datas:
            return None
        info_json = json.loads(preload_datas)
        infos = info_json.items()
        assert len(infos) == 3, "解析方式错误------all"
        _infos = []
        for _info in infos:
            _infos.append(_info)
        self.infos = _infos[1]
        del _infos
        if self.infos[0] == "illust":
            illust_infos = self.infos[1].popitem()
            self.work_id, work_info = illust_infos
            work_type = work_info.get("illustType")
            if work_type == 0:
                self.work_type = "illust"
            elif work_type == 1:
                self.work_type = "manga"
            elif work_type == 2:
                self.work_type = "ugoira"
            # illust_info = info_json.get("illust").get(id)
            # print(illust_info)
            self.work_info = work_info
            # self.result = self.fetch_artworks_links()
        elif self.infos[0] == "novel":
            novel_infos = self.infos[1].popitem()
            self.work_id, work_info = novel_infos
            self.work_type = "novel"
            self.work_info = work_info
            # self.result = self.fetch_novel()
        # self.work_type =

    def work_html_parser(self) -> dict | None:
        """
        work_html: pixiv作品详情页的html
            example url: https://www.pixiv.net/artworks/110099343
            example url: https://www.pixiv.net/novel/show.php?id=21223521
        """
        if self.infos[0] == "illust":
            illust_infos = self.infos[1].popitem()
            work_id, work_info = illust_infos
            work_type = work_info.get("illustType")
            if work_type == 0:
                work_type = "illust"
            elif work_type == 1:
                work_type = "manga"
            elif work_type == 2:
                work_type = "ugoira"
            # illust_info = info_json.get("illust").get(id)
            # print(illust_info)
        elif self.infos[0] == "novel":
            illust_infos = self.infos[1].popitem()
            work_id, work_info = illust_infos
            work_type = "novel"
        else:
            print(self.infos)
        # title1 = illust_info.get("illustTitle")
        title = work_info.get("title")
        # if title != title1:
        #     raise Exception("解析方式错误---title")
        # description1 = illust_info.get("illustComment")
        description = work_info.get("description")
        # if description1 != description:
        #     raise Exception("解析方式错误---description")
        # tags1 = work_info.get("tags").get("tags")
        tags = {}
        for text in work_info.get("tags").get("tags"):
            tag = text.get("tag")
            translation = text.get("translation")
            if translation:
                translation = translation.get("en")
            tags.update({tag: translation})
        # del tags1, title1, description1
        # all_url = re.search('(?<=urls":{).*?(?=})',info_2,re.S).group()
        userId = work_info.get("userId")
        username = work_info.get("userName")
        # userAccount = illust_info.get("userAccount")
        uploadDate = work_info.get("uploadDate")
        likeData = work_info.get("likeData")
        likeCount = work_info.get("likeCount")
        bookmarkCount = work_info.get("bookmarkCount")
        viewCount = work_info.get("viewCount")
        isOriginal = work_info.get("isOriginal")
        info = {
            "type": work_type,
            "id": int(work_id),
            "title": title,
            "description": description,
            "tags": tags,
            "userId": userId,
            "username": username,
            "uploadDate": uploadDate,
            "likeData": likeData,
            "likeCount": likeCount,             # 赞
            "bookmarkCount": bookmarkCount,     # 收藏
            "viewCount": viewCount,
            "isOriginal": isOriginal,           # 原创作品
        }
        if work_type == "novel":
            info.update(
                {"text": work_info.get("content"),  # 小说文本
                 "coverUrl": work_info.get("coverUrl")})
        return info

    async def fetch_artworks_links(self) -> dict:
        # title1 = illust_info.get("illustTitle")
        title = self.work_info.get("title")
        # if title != title1:
        #     raise Exception("解析方式错误---title")
        # description1 = illust_info.get("illustComment")
        description = self.work_info.get("description")
        # if description1 != description:
        #     raise Exception("解析方式错误---description")
        # tags1 = work_info.get("tags").get("tags")
        tags = {}
        for text in self.work_info.get("tags").get("tags"):
            tag = text.get("tag")
            translation = text.get("translation")
            if translation:
                translation = translation.get("en")
            tags.update({tag: translation})
        # del tags1, title1, description1
        # all_url = re.search('(?<=urls":{).*?(?=})',info_2,re.S).group()
        userId = self.work_info.get("userId")
        username = self.work_info.get("userName")
        # userAccount = illust_info.get("userAccount")
        uploadDate = self.work_info.get("uploadDate")
        likeData = self.work_info.get("likeData")
        likeCount = self.work_info.get("likeCount")
        bookmarkCount = self.work_info.get("bookmarkCount")
        viewCount = self.work_info.get("viewCount")
        isOriginal = self.work_info.get("isOriginal")
        info = {
            "type": self.work_type,
            "id": int(self.work_id),
            "title": title,
            "description": description,
            "tags": tags,
            "userId": userId,
            "username": username,
            "uploadDate": uploadDate,
            "likeData": likeData,
            "likeCount": likeCount,             # 赞
            "bookmarkCount": bookmarkCount,     # 收藏
            "viewCount": viewCount,
            "isOriginal": isOriginal,           # 原创作品
        }
        # ====================================
        #             获取原图链接
        # ====================================
        # 原图链接
        original_urls = []
        # 图片保存路径
        relative_path = []
        if self.work_type == "illust":
            xhr_url = "https://www.pixiv.net/ajax/illust/%s/pages?" % self.work_id
        elif self.work_type == "ugoira":
            xhr_url = "https://www.pixiv.net/ajax/illust/%s/ugoira_meta?" % self.work_id
        else:
            return None
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
            "referer": "https://www.pixiv.net/artworks/%s" % self.work_id}
        params = {"lang": "zh",
                  "version": "54b602d334dbd7fa098ee5301611eda1776f6f39"}
        # headers.update(
        #     {"referer": "https://www.pixiv.net/artworks/%d" % work_id})
        # requests = client.build_request("GET", xhr_url, params=params, headers=headers)
        # print(str(requests.url))
        error_count = 0
        while True:
            try:
                # 获取xhr返回的json
                res = await self.client.get(xhr_url, params=params, headers=headers)
                if res.is_success:
                    img_json = res.json()
                else:
                    error_count += 1
                    # self.logger.warning("获取作品信息失败\nID:%s------%d" % (work_id, res.status_code))
                    continue
            except httpx.ConnectTimeout:
                error_count += 1
                # self.logger.warning("连接超时!  请检查你的网络!")
            except httpx._exceptions as exc:
                error_count += 1
                img_json = None
                print(exc)
                # self.logger.debug(exc)
                # self.logger.error("获取作品信息失败\nID:%s" % id)
            finally:
                if error_count == 4:
                    # self.logger.info("自动重试失败!")
                    return None
                # self.logger.info("自动重试------%d/3" % error_count)
                if isinstance(img_json, dict):
                    if img_json.get("error"):
                        error_count += 1
                        # self.logger.info("访问错误------message:%s" % img_json.get("message"))
                    if error_count:
                        pass
                        # self.logger.info("自动重试成功!")
                break
        body = img_json.get("body")
        if self.work_type == "illust":
            for one in body:
                urls = one.get("urls")
                original = urls.get("original")
                name = re.search(r"[0-9]+\_.*", original).group()
                relative_path.append(
                    "picture/" + userId + "/" + name)
                original_urls.append(original)
        elif self.work_type == "ugoira":
            originalSrc = body.get("originalSrc")
            original_urls.append(originalSrc)
            name = re.search(r"[0-9]+\_ugoira", originalSrc).group()
            name = re.sub("_ugoira", ".gif", name)
            relative_path.append("picture/" + userId + "/" + name)
        info.update({'original_url': original_urls,
                    'relative_path': relative_path})
        for key in info:
            if info.get(key) is None and key != "description":
                raise Exception("解析方式错误---%s" % info)
        return info

    def fetch_series(self):
        pass

    def fetch_novel(self):
        # title1 = illust_info.get("illustTitle")
        title = self.work_info.get("title")
        # if title != title1:
        #     raise Exception("解析方式错误---title")
        # description1 = illust_info.get("illustComment")
        description = self.work_info.get("description")
        # if description1 != description:
        #     raise Exception("解析方式错误---description")
        # tags1 = work_info.get("tags").get("tags")
        tags = {}
        for text in self.work_info.get("tags").get("tags"):
            tag = text.get("tag")
            translation = text.get("translation")
            if translation:
                translation = translation.get("en")
            tags.update({tag: translation})
        # del tags1, title1, description1
        # all_url = re.search('(?<=urls":{).*?(?=})',info_2,re.S).group()
        userId = self.work_info.get("userId")
        username = self.work_info.get("userName")
        # userAccount = illust_info.get("userAccount")
        uploadDate = self.work_info.get("uploadDate")
        likeData = self.work_info.get("likeData")
        likeCount = self.work_info.get("likeCount")
        bookmarkCount = self.work_info.get("bookmarkCount")
        viewCount = self.work_info.get("viewCount")
        isOriginal = self.work_info.get("isOriginal")
        text = self.work_info.get("content")
        coverUrl = self.work_info.get("coverUrl")
        info = {
            "type": self.work_type,
            "id": int(self.work_id),
            "title": title,
            "description": description,
            "tags": tags,
            "userId": userId,
            "username": username,
            "uploadDate": uploadDate,
            "likeData": likeData,
            "likeCount": likeCount,             # 赞
            "bookmarkCount": bookmarkCount,     # 收藏
            "viewCount": viewCount,
            "isOriginal": isOriginal,           # 原创作品
            "text": text,  # 小说文本
            "coverUrl": coverUrl}
        for key in info:
            if info.get(key) is None and key != "description":
                raise Exception("解析方式错误---%s" % info)
        return info

    async def get_result(self):
        if self.infos[0] == "illust":
            result = await self.fetch_artworks_links()
        elif self.infos[0] == "novel":
            result = await self.fetch_novel()
        return result


class InfoGetter_old:
    """已弃用
    获取作品信息
    """
    __version = ''
    __proxies = ''

    def __init__(self, cookies: str, download_type: dict, db, backup_collection, logger,
                 progress_signal) -> None:
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

    def get_id(self, tag: str | None = None, uid: str | None = None) -> dict:
        """获取作者所有作品的id"""
        failure = False
        Ids = {}
        if tag is not None:
            pass

            # All_Ids['tag'] = Ids
            # 等待，防止封IP

        elif uid is not None:
            # self.logger.info("获取作者{}的作品id".format(uid))
            self.headers.update(
                {"referer": "https://www.pixiv.net/users/{}".format(uid)})
            xhr_url = (
                "https://www.pixiv.net/ajax/user/{}/profile/all?lang=zh&version={}".format(
                    uid, self.__version)
            )
            try:
                ids_json = requests.get(
                    xhr_url,
                    headers=self.headers,
                    cookies=self.cookies,
                    proxies=self.__proxies,
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
                            proxies=self.__proxies,
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

    def get_info(self, url: str, id: str) -> dict:
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
                proxies=self.__proxies,
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
                    proxies=self.__proxies,
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
                id, self.__version)
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
                proxies=self.__proxies,
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
                        proxies=self.__proxies,
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

    def stop_getting(self):
        self.event.clear()
        self.logger.info("停止获取作者的作品信息")
