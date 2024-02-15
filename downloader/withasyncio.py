# -*-coding:utf-8-*-
import httpx
import glob
import json
import os
import re
import time
import zipfile
import aiohttp
import asyncio
from PIL import Image
import http.cookies
http.cookies._is_legal_key = lambda _: True


class DownloaderHttpx:
    """
    下载图片
    TODO 下载小说

    Attributes:
        __proxies: Proxy to use aiohttp to send HTTP requests (optional)
        __event: The stop event
        db: The database connection of MongoDB(async)
        cookies: The cookies when a request is sent to pixiv
        host_path: The root path where the image to be saved
        download_type: The type of work to be downloaded
        backup_collection: A collection of backup of info(async)
        logger: The instantiated object of logging.Logger
        progress_signal: The pyqtSignal of QProgressBar
        headers: The headers when sending a HTTP request to pixiv
        timeout: The timeout period for aiohttp requests
        semaphore: The concurrent semaphore of asyncio
    """

    __proxies = 'http://localhost:1111'
    __event = asyncio.Event()

    def __init__(self, host_path: str, cookies: dict, download_type: dict, semaphore: int, backup_collection, logger) -> None:
        self.cookies = cookies
        self.host_path = host_path
        self.download_type = download_type
        self.backup_collection = backup_collection
        self.logger = logger
        self.headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
                 Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
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

    async def start_work_download(self, id):
        """
        从图片url下载
        """
        print("开始下载")
        tasks = []
        import infofetcher
        infogetter = infofetcher.InfoGetterOld(
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
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies, timeout=self.timeout) as session:
            for a in range(len(urls)):
                if not self.__event.is_set():
                    return
                url = urls[a]
                name = re.search(r"[0-9]+\_.*", url).group()
                path = self.host_path + "works/" + id + "/" + name
                relative_path.append("works/" + id + "/" + name)
                # 检测是否已下载
                if not os.path.isfile(path=path):
                    info = (id, url, path)
                    tasks.append(asyncio.create_task(
                        self.bound_download_image_async(session, info)))
            infos.update({"relative_path": relative_path})
            with open(
                "{}works/{}/info.json".format(self.host_path, id), "w", encoding="utf-8"
            ) as f:
                json.dump(infos, f, ensure_ascii=False, indent=4)
            await asyncio.wait(tasks)

        print("下载完成")

    def start_tag_download(self):
        """
        从pixiv获取含标签的图片下载
        """

    async def start_following_download(self):
        """
        从mongodb中获取图片url并放进协程队列
        """
        self.logger.info("开始下载\n由于需要读取数据库信息并检测是否下载,所以可能等待较长时间")
        tasks = []
        async for doc in self.backup_collection.find({"id": {"$exists": True}}):
            if not self.__event.is_set():
                return
            tasks.clear()
            if doc.get("failcode"):
                continue
            if not self.download_type.get("get" + doc.get("type")):
                if not self.download_type.get("get" + doc.get("type") + "s"):
                    self.logger.warning("作品%s不在下载类型%s中" %
                                        (doc.get("id"), "get" + doc.get("type")))
                    continue
                # print(doc)
            id = doc.get("id")
            urls = doc.get("original_url")
            uid = doc.get("userId")
            paths = doc.get("relative_path")
            if len(paths) < 1:
                self.logger.warning("数据错误:\n%s" % str(doc))
                continue

            for a in range(len(urls)):
                if not self.__event.is_set():
                    return
                try:
                    url = urls[a]
                    path = self.host_path + paths[a]
                except Exception:
                    print(doc)
                    continue

                # 检测保存路径是否存在,不存在则创建
                if os.path.isdir(self.host_path + "/picture/" + uid + "/") is False:
                    os.makedirs(self.host_path + "/picture/" + uid + "/")
                # 检测是否已下载
                if not os.path.isfile(path=path):
                    info = (id, url, path)
                    tasks.append(asyncio.create_task(
                        self.download_image(info)))
            if tasks:
                await asyncio.gather(*tasks)
        self.logger.info("下载完成")

    async def invalid_image_recorder(self, id, failcode):
        doc = await self.backup_collection.find_one_and_update(
            {"id": id}, {"$set": {"failcode": failcode}}
        )
        if not doc:
            self.logger.error(
                "error in record invaild image:" + id + "\n" + doc)

    async def stream_download(self, request_info: tuple, path: str):
        """
        流式接收数据并写入文件
        """
        url, headers = request_info
        error_count = 0
        while True:
            try:
                if not self.__event.is_set():
                    return 0
                async with self.client.stream("GET", url, headers=headers) as response:
                    if response.status_code != 200:
                        if error_count >= 3:
                            self.logger.warning("自动重试失败!")
                            # 错误记录，但感觉没什么用
                            # self.failure_recoder_mongo(id)
                            return response.status_code
                        error_count += 1
                        self.logger.warning("下载失败!---响应状态码:%d" %
                                            response.status_code)
                        self.logger.info("自动重试---%d/3" % error_count)
                        continue
                    else:
                        f = open(path, "wb")
                        async for chunk in response.aiter_bytes(chunk_size=1024):
                            if not self.__event.is_set():
                                f.close()
                                os.remove(path)
                                return 0
                            f.write(chunk)
                            f.flush()
                        f.close()
                        return 0
            except Exception:
                error_count += 1
                if error_count >= 3:
                    return 1
                self.logger.warning("下载失败!")
                self.logger.info("自动重试---%d/3" % error_count)
                time.sleep(3)
                continue

    async def download_image(self, info: tuple):
        """从队列中获取数据并下载图片"""
        async with self.semaphore:
            if not self.__event.is_set():
                return
            start_time = time.time()  # 程序开始时间
            # print('获取数据%s'%(info))
            id = str(info[0])
            url = info[1]
            path = info[2]
            if re.search(r"ug", url, re.S) is not None:
                return
                if re.search(r"ugoira", url) is not None:
                    cover_url = url
                else:
                    info = re.search(r"img/.*", url).group()
                    zip_url = "https://i.pximg.net/img-zip-ugoira/" + info + "oira1920x1080.zip"
                save_name = id + ".zip"
                image_dir = id + "/"
                self.logger.info("下载动图ID:%s" % id)
                failcode = await self.stream_download((zip_url, self.headers), save_name)
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
                gif_images = [Image.open(image_path)
                              for image_path in image_list]
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
                failcode = await self.stream_download((url, self.headers), path)
                if failcode:
                    if failcode != 1:
                        self.logger.warning(
                            "下载图片%s失败------%s" % (id, failcode))
                        await self.invalid_image_recorder(int(id), failcode)
                        return
                    else:
                        self.logger.error("下载图片%s失败" % id)
                        return
            if not self.__event.is_set():
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
        self.__event.clear()
        self.logger.info("停止下载")
        return


class Downloader:
    """
    下载图片
    TODO 下载小说

    Attributes:
        __proxies: Proxy to use aiohttp to send HTTP requests (optional)
        __event: The stop event
        db: The database connection of MongoDB(async)
        cookies: The cookies when a request is sent to pixiv
        host_path: The root path where the image to be saved
        download_type: The type of work to be downloaded
        backup_collection: A collection of backup of info(async)
        logger: The instantiated object of logging.Logger
        progress_signal: The pyqtSignal of QProgressBar
        headers: The headers when sending a HTTP request to pixiv
        timeout: The timeout period for aiohttp requests
        semaphore: The concurrent semaphore of asyncio
    """

    __proxies = ''  # 'http://localhost:1111'
    __event = asyncio.Event()

    def __init__(self, host_path: str, cookies: dict, download_type: dict, semaphore: int, backup_collection, logger) -> None:
        self.cookies = cookies
        self.host_path = host_path
        self.download_type = download_type
        self.backup_collection = backup_collection
        self.logger = logger
        self.headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)\
                 Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188",
            "referer": "https://www.pixiv.net/"}
        self.timeout = aiohttp.ClientTimeout(total=5)
        self.semaphore = asyncio.Semaphore(semaphore)
        self.__event.set()

    async def start_work_download_async(self, id):
        """
        从图片url下载
        """
        print("开始下载")
        tasks = []
        import infofetcher
        infogetter = infofetcher.InfoGetterOld(
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
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies, timeout=self.timeout) as session:
            for a in range(len(urls)):
                if not self.__event.is_set():
                    return
                url = urls[a]
                name = re.search(r"[0-9]+\_.*", url).group()
                path = self.host_path + "works/" + id + "/" + name
                relative_path.append("works/" + id + "/" + name)
                # 检测是否已下载
                if not os.path.isfile(path=path):
                    info = (id, url, path)
                    tasks.append(asyncio.create_task(
                        self.bound_download_image_async(session, info)))
            infos.update({"relative_path": relative_path})
            with open(
                "{}works/{}/info.json".format(self.host_path, id), "w", encoding="utf-8"
            ) as f:
                json.dump(infos, f, ensure_ascii=False, indent=4)
            await asyncio.wait(tasks)

        print("下载完成")

    def start_tag_download(self):
        """
        从pixiv获取含标签的图片下载
        """

    async def start_following_download_async(self):
        """
        从mongodb中获取图片url并放进协程队列
        """
        self.logger.info("开始下载\n由于需要读取数据库信息并检测是否下载,所以可能等待较长时间")
        tasks = []
        async with aiohttp.ClientSession(headers=self.headers, cookies=self.cookies, timeout=self.timeout) as session:
            async for doc in self.backup_collection.find({"id": {"$exists": True}}):
                if not self.__event.is_set():
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
                    if not self.__event.is_set():
                        return
                    try:
                        url = urls[a]
                        path = self.host_path + paths[a]
                    except Exception:
                        print(doc)
                        continue

                    # 检测保存路径是否存在,不存在则创建
                    if os.path.isdir(self.host_path + "/picture/" + uid + "/") is False:
                        os.makedirs(self.host_path + "/picture/" + uid + "/")
                    # 检测是否已下载
                    if not os.path.isfile(path=path):
                        info = (id, url, path)
                        tasks.append(asyncio.create_task(
                            self.bound_download_image_async(session, info)))
                if tasks:
                    await asyncio.gather(*tasks)
        self.logger.info("下载完成")

    async def invalid_image_recorder(self, id, failcode):
        doc = await self.backup_collection.find_one_and_update(
            {"id": id}, {"$set": {"failcode": failcode}}
        )
        if not doc:
            self.logger.error(
                "error in record invaild image:" + id + "\n" + doc)

    async def stream_download_async(self, session: aiohttp.ClientSession, request_info: tuple, path: str):
        """
        流式接收数据并写入文件
        """
        url, headers = request_info
        error_count = 0
        while 1:
            try:
                if not self.__event.is_set():
                    return 0
                response = await session.get(
                    url,
                    headers=headers,
                    proxy=self.__proxies,
                )
            except Exception:
                error_count += 1
                if error_count == 4:
                    return 1
                self.logger.warning("下载失败!")
                self.logger.info("自动重试---%d/3" % error_count)
                time.sleep(3)
                continue
            if response.status != 200:
                error_count += 1
                if error_count == 4:
                    return response.status
                self.logger.warning("下载失败!---响应状态码:%d" %
                                    response.status)
                self.logger.info("自动重试---%d/3" % error_count)
                time.sleep(1)
                continue
            else:
                break
        if error_count == 3:
            self.logger.info("自动重试失败!")
            # 错误记录，但感觉没什么用
            # self.failure_recoder_mongo(id)
            return response.status
        f = open(path, "wb")
        while True:
            if not self.__event.is_set():
                f.close()
                os.remove(path)
                return 0
            chunk = await response.content.read(1024)
            if not chunk:
                break
            f.write(chunk)
            f.flush()
        f.close()
        return 0

    async def bound_download_image_async(self, session: aiohttp.ClientSession, info: tuple):
        async with self.semaphore:
            await self.download_image_async(session, info)

    async def download_image_async(self, session: aiohttp.ClientSession, info: tuple):
        """从队列中获取数据并下载图片"""
        if not self.__event.is_set():
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
            failcode = await self.stream_download_async(session, (zip_url, self.headers), save_name)
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
            failcode = await self.stream_download_async(session, (url, self.headers), path)
            if failcode:
                if failcode != 1:
                    self.logger.warning("下载图片%s失败------%s" % (id, failcode))
                    await self.invalid_image_recorder(int(id), failcode)
                    return
                else:
                    self.logger.error("下载图片%s失败" % id)
                    return
        if not self.__event.is_set():
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
        self.__event.clear()
        self.logger.info("停止下载")
        return
