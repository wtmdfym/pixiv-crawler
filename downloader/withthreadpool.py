# -*-coding:utf-8-*-
import glob
import json
import os
import re
import threading
import time
import zipfile
import requests
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

proxie = ''  # {'http': 'http://localhost:1111', 'https': 'http://localhost:1111'}


class Downloader:
    """
    下载图片
    TODO 下载小说
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
        import infofetcher
        infogetter = infofetcher.InfoGetter(
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
                proxies=proxie,
                stream=True,
                timeout=5,
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
                        proxies=proxie,
                        stream=True,
                        timeout=5,
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
        '''
        with open(path, "wb") as f:
            f.write(response.content)
            f.flush()
        '''
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
