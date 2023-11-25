import requests
import aiohttp
import asyncio
import time
import re
"""
    aiohttp:发送http请求
    1.创建一个ClientSession对象
    2.通过ClientSession对象去发送请求（get, post, delete等）
    3.await 异步等待返回结果
"""

timeout = aiohttp.ClientTimeout(total=10)


imagelist = [
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p0.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p1.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p2.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p3.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p4.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p5.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p6.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p7.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p8.png",
    "https://i.pximg.net/img-original/img/2023/01/13/13/18/52/104476868_p9.png"]


async def fetch_image(session: aiohttp.ClientSession, url: str, path: str) -> None:
    async with session.get(url, proxy='http://localhost:1111') as res:
        if res.status != 200:
            print(res.status)
        # <StreamReader 8202 bytes>
        print(res.content)
        with open(path, 'wb') as fd:
            # async for chunk in res.content.iter_chunked(1024):
            while True:
                chunk = await res.content.read()
                if not chunk:
                    break
                pass
                fd.write(chunk)


async def request(client):
    resp = await client.get('https://www.pixiv.net/ajax/user/53184612?full=0',
                            proxy='http://localhost:1111', trust_env=True,)
    result = await resp.json()
    print(result)


async def main():
    # url = 'http://httpbin.org/get'
    # url = 'http://httpbin.org/cookies'
    # url = 'https://api.github.com/events'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36\
             (KHTML, like Gecko) Chrome/69.0.3947.100 Safari/537.36', 'referer': 'https://www.pixiv.net/artworks/113102650'}
    cookies = {}  # {'cookies_are': 'working'}
    async with aiohttp.ClientSession(headers=headers, cookies=cookies, timeout=timeout) as session:
        start = time.time()
        task_list = []
        path = "./testaio/{}.png"
        for a in range(len(imagelist)):
            path1 = path.format(a)
            # req = request(session)
            req = fetch_image(session, imagelist[a], path1)
            task = asyncio.create_task(req)
            task_list.append(task)
        await asyncio.gather(*task_list)
        end = time.time()
        print(end-start)


def fetch_image2(session: requests.Session, url: str, path: str) -> None:
    with session.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
         Chrome/69.0.3947.100 Safari/537.36', 'referer': 'https://www.pixiv.net/artworks/113102650'}, stream=True, proxies={'http': 'http://localhost:1111', 'https': 'http://localhost:1111'}) as res: 
        # 
        if res.status_code != 200:
            print(res.status_code)
        # print(res.content)
        with open(path, 'wb') as fd:
            for chunk in res.iter_content(1024):
                pass
                fd.write(chunk)


def fetch_image3(url: str, proxy_info) -> None:
    with requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)\
         Chrome/69.0.3947.100 Safari/537.36', 'referer': 'https://www.pixiv.net/artworks/113102650'}, stream=True, proxies={"http": "http://{}".format(proxy_info.get("proxy"))}) as res:
        if res.status_code != 200:
            print(res.status_code)
        print(res.content)
        for chunk in res.iter_content(1024):
            pass
            # fd.write(chunk)


def main2():
    session = requests.Session()
    start = time.time()
    path = "./testaio2/{}.png"
    for a in range(len(imagelist)):
        path1 = path.format(a)
        # req = request(session)
        req = fetch_image2(session, imagelist[a], path1)
    """
    for _ in range(5):
        # resp = session.get('https://www.pixiv.net/ajax/user/53184612?full=0')
        # result = resp.json()
        # print(result)
        fetch_image2(
            session, 'https://i.pximg.net/c/250x250_80_a2/img-master/img/2023/11/04/18/01/12/113132058_p0_square1200.jpg')
        # proxy_info = get_and_check_proxy()
        # if proxy_info:
        #     fetch_image3('https://i.pximg.net/c/250x250_80_a2/img-master/img/2023/11/04/18/01/12/113132058_p0_square1200.jpg', proxy_info)
    """
    end = time.time()
    print(end-start)


def get_and_check_proxy():
    proxy_info = requests.get("http://127.0.0.1:5010/get/").json()
    resp = requests.get('https://www.pixiv.net/artworks/113102650', timeout=5,
                        proxies={"http": "http://{}".format(proxy_info.get("proxy"))})
    if resp.status_code == 200:
        return proxy_info
    else:
        print(resp)
        delete_proxy(proxy_info.get("proxy"))


def delete_proxy(proxy):
    requests.get("http://127.0.0.1:5010/delete/?proxy={}".format(proxy))


def check_proxy():
    proxy_infos = requests.get("http://127.0.0.1:5010/all/").json()
    for proxy_info in proxy_infos:
        resp = requests.get('https://www.pixiv.net/artworks/113102650', timeout=5,
                            proxies={"http": "http://{}".format(proxy_info.get("proxy"))})
        if resp.status_code == 200:
            return proxy_info
        else:
            print(resp)
            delete_proxy(proxy_info.get("proxy"))
    print(requests.get("http://127.0.0.1:5010/all/").json())


if __name__ == '__main__':
    asyncio.run(main())
    # loop = asyncio.get_event_loop()
    # task = loop.create_task(main())
    # loop.run_until_complete(task)
    # main2()
    # check_proxy()
    # print(get_and_check_proxy())
    # resp = requests.get('https://www.pixiv.net/artworks/113102650', timeout=5,
    #                     proxies={'http': 'http://localhost:1111', 'https': 'http://localhost:1111'})
    # print(resp.status_code)
