# -*-coding:utf-8-*-
import json
import os
import re
import http.cookies
from urllib import parse

http.cookies._is_legal_key = lambda _: True

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
    def get_config(cls, config_file_path: str, default_config_save_path: str) -> dict:
        if os.path.exists(config_file_path):
            with open(config_file_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        else:
            with open(default_config_save_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
        return config_dict

    @classmethod
    def set_config(cls, config_file_path: str, config_dict: dict) -> None:
        with open(config_file_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=4)


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
            key = re.sub(' ', '', key)
            value = re.sub(' ', '', value)
            cookies[key] = value
        return cookies


if __name__ == "__main__":
    a = "{'afaf':'a5af','fw':8464}"
    b = "_gcl_au=1.1.1140122344.1692758372; login_ever=yes; c_type=24;"
    print(eval(a))
    print(eval(b))
