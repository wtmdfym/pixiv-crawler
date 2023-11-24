#-*-coding:utf-8-*-
import requests,json,time,re,os,zipfile,html,glob,threading,sys
from PIL import Image
from urllib import parse
import urllib3.exceptions
from concurrent.futures import ThreadPoolExecutor,as_completed
urllib3.disable_warnings()

#代理
proxie = ''

version='12bf979348f8a251a88224d94a7ba55705d943fe'

config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),'config.json')

download_type = dict(Getillusts=True,Getmanga=True,GetmangaSeries=False,GetnovelSeries=False,Getnovels=False)

class Tools:
    
    def __init__(self) -> None:
        pass
    
    def compare_datetime(lasttime:str,newtime:str)->bool:
        time1 = [lasttime[0:4],lasttime[4:6],lasttime[6:8]]
        time2 = [newtime[0:4],newtime[4:6],newtime[6:8]]
        #print(time1,time2)
        if time2[0]>time1[0]:
            return True
        elif time2[0]==time1[0]:
            if time2[1]>time1[1]:
                return True
            elif time2[1]==time1[1]:
                return time2[2]>time1[2]
        return False

    def search(collection, search_info, page_number):
        all_founded=[]
        work_number=0

        if re.findall("\+",search_info):
            and_search = []
            for one_search in search_info.split("+"):
                if re.search("\d{4,}",one_search):
                    and_search.append({"userId":one_search})
                else:and_search.append({'tags.'+one_search:{'$exists': 'true'}})
            results = collection.find({"$and":and_search}).sort("id",-1)
            #self.results = collection.find({"$and":and_search})
            #self.work_number = collection.find({"$and":and_search})
            
        elif re.findall("\,",search_info):
            or_search = []
            for one_search in search_info.split(","):
                if re.search("\d{4,}",one_search):
                    or_search.append({"userId":one_search})
                else:or_search.append({'tags.'+one_search:{'$exists': 'true'}})
                results = collection.find({"$or":or_search}).sort("id",-1)
        
        else:
            one_search ={}
            if re.search("\d{4,}",search_info):
                one_search.update({"userId":search_info})
            else:one_search.update({'tags.'+search_info:{'$exists': 'true'}})
            results = collection.find(one_search).sort("id",-1)

        for row in results:
            all_founded.append(row)
            work_number += 1
            #print(row.get("id"))
        total_page = (work_number - 1) // (page_number) + 1
        return all_founded,total_page

    def show_img(path:str, img_canva, img_sizes:tuple):
        from PIL import ImageTk,UnidentifiedImageError
        img_canva.delete("all")

        if re.search("\.gif",path):
            #self.images.update({index:'gif'})
            img_canva.create_text(0, 0, text = "This is a gif,double click\nleft mouse button if you want see it", anchor='nw')
        else:
            if os.path.exists(path):
                try:loaded_image = Image.open(path)
                except UnidentifiedImageError:os.remove(path)
                if loaded_image:
                    original_width, original_height = loaded_image.size
                    aspect_ratio = original_width / original_height
                    if aspect_ratio > 1:
                        new_width = min(original_width, img_sizes[0])
                        new_height = int(new_width / aspect_ratio)
                    else:
                        new_height = min(original_height, img_sizes[1])
                        new_width = int(new_height * aspect_ratio)
                    resized_image = loaded_image.resize((new_width, new_height))
                    image = ImageTk.PhotoImage(resized_image)
                    img_canva.create_image(0, 0, image=image, anchor='nw')
                    return image
                else:
                    img_canva.create_text(0, 0, text = "未下载图片或移动了图片", anchor='nw')
            else:
                img_canva.create_text(0, 0, text = "未下载图片或移动了图片", anchor='nw')

class Analyzer:
    
    def __init__(self, database_client) -> None:
        self.db = database_client['pixiv']

    def tag_to_url(tag)->str:
        '''URL编码'''
        url = parse.quote(tag)
        return url

    def failure_recoder_mongo(self,id:int):
        collection = self.db['failures']
        if collection.find_one({'id':id}):print('错误已记录')
        else:
            res = collection.insert_one({'id':id})
            if res:
                print('记录错误成功')

    def analyze_input(input_info)->list:
        if not input_info:return None
        uids = []
        tags = []
        infos1 = input_info
        if re.search('，',infos1):
            print('输入格式错误!!!')
            return None
        infos=infos1.split(',')
        for info in infos:
            uid =  re.search('[0-9]+',info)
            if uid != None:
                uids.append(uid.group())
            else:tags.append(info)
        if (len(uids) and len(tags)):
            print('输入格式错误!!!')
            return None
        return [uids,tags]

class ConfigSetter:
    def __init__(self) -> None:
        pass

class FollowingsRecorder:
    '''
    获取已关注的用户的信息
    '''
    def __init__(self, cookies, database):
        self.cookies = cookies
        self.db = database
        self.followings_collection = self.db["All Followings"]

    def following_recorder(self):
        print('正在获取已关注作者的信息......')
        url = 'https://www.pixiv.net/ajax/user/extra?lang=zh&version={version}'.format(version=version)
        headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.188',
                    'referer': 'https://www.pixiv.net/users/83945559/following?p=1'}
        try:
            response=requests.get(url=url, headers=headers, cookies=self.cookies, proxies=proxie, verify=False, timeout=5).json()
        except requests.exceptions.JSONDecodeError:
            raise Exception('[ERROR]-----无法访问pixiv,检查你的网络连接')
        except requests.exceptions.ConnectionError:
            raise Exception('[ERROR]-----无法访问pixiv,检查你的网络连接')
        if response.get("error"):
            raise Exception('请检查你的cookie是否正确',response)
        body=response.get('body')
        following=body.get('following')
        following_infos = self.get_my_followings(following)
        #print(followings)
        for a in range(len(following_infos)):
            following = following_infos.pop()
            userId = following.get('userId')
            if userId=="11":continue
            earlier = self.followings_collection.find_one({'userId':userId})
            userName = following.get('userName')
            userComment = following.get('userComment')
            if earlier:
                print('Have been recorded:%s'%({'userId':userId,'userName':userName}))
                earlier_userName = earlier.get('userName')
                earlier_userComment = earlier.get('userComment')
                if earlier_userName != userName:
                    print('Updating:%s to %s'%(earlier_userName,userName))
                    self.rename_collection(earlier_userName,userName)
                    #make sure update is successful
                    a = self.followings_collection.update_one({"userId":userId}, {"$set": {"userName":userName}})
                    if a:print('Update Success')
                    else:raise Exception('update failed')
                if earlier_userComment != userComment:
                    print('Updating userComment......')
                    a = self.followings_collection.update_one({"userId":userId}, {"$set": {"userComment":userComment}})
                    if a:print('Update Success')
                    else:raise Exception('Update Failed')
            else:
                print('recording:{}'.format({'userId':userId, 'userName':userName}))
                self.followings_collection.insert_one({'userId':userId, 'userName':userName})
        print("获取已关注的作者信息完成")

    def get_my_followings(self,following):
        following_url = 'https://www.pixiv.net/ajax/user/83945559/following?offset={offset}&limit=24&rest=show&tag=&acceptingRequests=0&lang=zh&version={version}'
        userinfos=[]
        all_page = following//24+1
        for page in range(all_page):
            #time.sleep(0.5)
            headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3947.100 Safari/537.36',
                    'referer': 'https://www.pixiv.net/users/83945559/following?p='+str(page)}
            following_url1 = following_url.format(offset=page*24,version=version)
            response=requests.get(url=following_url1, verify=False, headers=headers, cookies=self.cookies, proxies=proxie).json()
            body = response.get('body')
            users = body.get('users')
            for user in users:
                userId = user.get('userId')
                userName = user.get('userName')
                userComment = user.get('userComment')
                userinfos.append({'userId':userId,'userName':userName,'userComment':userComment})
            done = int(50 * page / (all_page-1))
            sys.stdout.write("\r[%s%s] %d%%" % ('█' * done, ' ' * (50 - done), 100 * page / (all_page-1)))
            sys.stdout.flush()
        print('\n')
        return userinfos

    def rename_collection(self,name1,name2):
        """
        当关注的作者更改名字时重命名集合
        :name1 原来的集合名字
        :name2 新的集合名字
        """
        print('重命名数据库......')
        collection_1 = self.db[name1]
        collection_2 = self.db[name2]
        for doc in collection_1.find({"id": { "$exists": True }}):
            #print(doc)
            doc.update({"username":name2})
            collection_2.insert_one(doc)
        collection_1.drop()

class InfoGetter:
    '''
    获取作品信息
    '''
    def __init__(self, cookies, download_type, db, backup_collection) -> None:
        self.db = db
        self.cookies = cookies
        self.download_type = download_type
        self.backup_collection = backup_collection
        self.event = threading.Event()
        self.event.set()

    def start_get_info(self):
        finish = self.record_infos()
        if finish:
            success = self.mongoDB_auto_backup()
            if success:return True
            else:raise Exception('database backup error')

    def record_infos(self):
        self.followings_collection = self.db["All Followings"]
        painters = self.followings_collection.find({"userId": { "$exists": True }})
        for  painter in painters:
            uid = painter.get("userId")
            name = painter.get("userName")
            print('-------------爬取%s的作品信息-------------'%(uid))
            collection = self.db[name]
            ids = self.get_id(uid=uid)
            if ids:
                self.record_info_mongodb(ids=ids,collection=collection)
            print('------------爬取%s的作品信息完成------------'%(uid))
            if not self.event.is_set():
                return False

        timeint = int(time.strftime("%Y%m%d%H%M%S"))
        with open(config_path,'r',encoding='utf-8') as f:
            json_data = json.load(f)
            json_data.update({"last_record_time":timeint})
        with open(config_path,'w',encoding='utf-8') as f:
            json.dump(json_data,f,ensure_ascii=False)
        print("------------爬取所有作品信息完成------------\n")
        return True

    def get_id(self,tag = None,uid = None)->dict:
        '''获取作品的id'''
        failure = False
        Ids = {}
        referer = None
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3947.100 Safari/537.36',
            'referer': referer}
        if tag != None:
            pass
            
            #All_Ids['tag'] = Ids
            #等待，防止封IP
            time.sleep(1)
        
        elif uid != None:
            print('获取作者{}的作品id'.format(uid))
            referer = 'https://www.pixiv.net/users/' + str(uid)
            xhr_url = 'https://www.pixiv.net/ajax/user/' + str(uid) + '/profile/all?lang=zh&version={}'.format(version)
            try:ids_json = requests.get(xhr_url, headers=headers, cookies=self.cookies, proxies=proxie, verify=False).json()
            except:
                print('[ERROR]获取ID失败')
                for a in range(1,4):
                    print('自动重试---%d/3'%(a))
                    time.sleep(3)
                    try:
                        ids_json = requests.get(xhr_url, headers=headers, cookies=self.cookies, proxies=proxie, verify=False).json()
                        if ids_json != None:
                            print('自动重试成功!')
                            break
                    except:
                        print('自动重试失败!')
                        if a == 3:failure = True
            if failure:return None
            body = ids_json.get('body')
            if type(body) is not dict:
                #raise Exception('[ERROR]获取ID失败!',body)
                print('[ERROR]获取ID失败!')
                print(ids_json)
                return None
            #插图
            illusts = []
            illusts1 = body.get("illusts")
            if type(illusts1) == dict and illusts1 != None:
                for illust in illusts1.keys():
                    illusts.append(illust)
            elif len(illusts) < 1:pass
            else:raise Exception('[ERROR]获取插画失败!')
            #漫画
            manga = []
            manga1 = body.get("manga")
            if type(manga1) == dict and manga1 != None:
                for manga2 in manga1.keys():
                    manga.append(manga2)
            elif len(manga) < 1:manga = []
            else:raise Exception('[ERROR]获取漫画失败!')
            #漫画系列
            mangaSeries = str(re.findall("'mangaSeries'.*?}]",str(ids_json),re.S))
            #小说系列
            novelSeries = str(re.findall("'novelSeries'.*?}]",str(ids_json),re.S))
            #小说
            novels = str(re.findall("'novels'.*?}]",str(ids_json),re.S))
            
            #reeturn ids
            if len(illusts) != 0 and self.download_type.get('Getillusts'):
                Ids['illusts'] = illusts
            if len(manga) != 0 and self.download_type.get('Getmanga'):
                Ids['manga'] = manga
            if len(mangaSeries) != 0 and self.download_type.get('GetmangaSeries'):
                mangaSeries_1 = str(re.findall("'id':.*?,",mangaSeries,re.S))
                mangaSeries_ids = re.findall("[0-9]+",mangaSeries_1,re.S)
                Ids['mangaSeries'] = mangaSeries_ids
            if len(novelSeries) != 0 and self.download_type.get('GetnovelSeries'):
                novelSeries_1 = str(re.findall("'id':.*?,",novelSeries,re.S))
                novelSeries_ids = re.findall("[0-9]+",novelSeries_1,re.S)
                Ids['novelSeries'] = novelSeries_ids
            if len(novels) != 0 and self.download_type.get('Getnovels'):
                novels_1 = str(re.findall("'id':.*?,",novels,re.S))
                novels_ids = re.findall("[0-9]+",novels_1,re.S)
                Ids['novels'] = novels_ids
            #等待，防止封IP
            time.sleep(0.5)
        return Ids

    def get_info(self,url,id)->dict:
        """
        获取图片详情信息
        illust_info:如果要爬其他类型的作品时不一样!
        """
        fail = False
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        try:
            work_html = requests.get(url=url, headers=headers, cookies=self.cookies, proxies=proxie, verify=False).text
        except:fail = True
        if (len(work_html) <= 100) or re.search('error-message',work_html,re.S) or fail:
            print('获取html失败!')
            for a in range(1,4):
                print('自动重试---%d/3'%(a))
                time.sleep(5)
                work_html = requests.get(url=url, headers=headers, cookies=self.cookies, proxies=proxie, verify=False).text
                if len(work_html) >= 100:
                    print('自动重试成功!')
                    break
                else:
                    print('自动重试失败!')
        try:
            info_1 = re.search('\<meta.name="preload-data".*?\>',work_html,re.S).group()
        except:
            print('获取html失败!')
            #print(work_html+"\n\n")
            print(url)
            return
        info_json = json.loads(re.search("(?<=content=').*?(?=')",info_1,re.S).group())
        illust_info = info_json.get("illust").get(id)
        #print(illust_info)
        work_type = illust_info.get("illustType")
        title1 = illust_info.get("illustTitle")
        title = illust_info.get("title")
        if title != title1:raise Exception("解析方式错误---title")
        description1 = illust_info.get("illustComment")
        description_1 = illust_info.get("description")
        if description1 != description_1:raise Exception("解析方式错误---description")
        #handle html escape characters with html
        description = html.unescape(description_1)
        #if don't unescape completely, use this:
        if re.search("&#\d",description,re.S):
            description = html.unescape(description)
        #remove <br> and <a>
        description = re.sub('<br.*?/>','\n',description)
        description = re.sub('<a href=.*?target="_blank">','',description)
        description = re.sub('</a>','',description)
        #print(description)

        tags1 = illust_info.get("tags").get("tags")
        local_var_tags = {}
        for text in tags1:
            tag = text.get("tag")
            translation = text.get("translation")
            if translation: translation= translation.get("en")
            local_var_tags.update({tag:translation})
        # all_url = re.search('(?<=urls":{).*?(?=})',info_2,re.S).group()
        userId = illust_info.get("userId")
        username = illust_info.get("userName")
        # userAccount = illust_info.get("userAccount")
        # 解析原图链接
        original_urls=[]
        # 图片保存路径
        relative_path = []
        referer = 'https://www.pixiv.net/artworks/' + id
        xhr_url = 'https://www.pixiv.net/ajax/illust/'+ id+'/pages?lang=zh&version={}'.format(version)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36','referer':referer}
        try:
            #=======================================================
            # 获取xhr返回的json
            img_json = requests.get(xhr_url, headers=headers, cookies=self.cookies, verify=False, proxies=proxie).json()
        except:
            print('[ERROR]获取链接失败ID%s'%(id))
            for a in range(1,4):
                print('自动重试---%d/3'%(a))
                time.sleep(5)
                try:
                    img_json = requests.get(xhr_url, headers=headers, cookies=self.cookies, verify=False, proxies=proxie).json()
                    if img_json != None:
                        print('自动重试成功!')
                        break
                except:
                    print('自动重试失败!')
        body = img_json.get("body")
        for one in body:
            urls = one.get("urls")
            original = urls.get("original")
            #检测是否是动图
            if re.search('_ugoira0',original):original = re.sub('_ugoira0.*','_ug',original)
            name = re.search('[0-9]+\_.*',str(original)).group()
            if re.search('_ug',name):name = re.sub('_ug','.gif',name)
            relative_path.append('picture/'+userId+'/'+name)
            original_urls.append(original)
        info ={'id':int(id),'title':title,'description':description,'tags':local_var_tags,'original_url':original_urls,
            'userId':userId,'username':username,'relative_path':relative_path}
        
        for key in info:
            if info[key] == None and key != 'description':
                raise Exception("解析方式错误---%s"%info)
        return info

    def record_in_tags(self, tags):
        self.tags_collection = self.db["All Tags"]
        for a in range(len(tags)):
            name,translate = tags.popitem()
            earlier = self.tags_collection.find_one({'name':name})
            if earlier:
                if earlier.get('translate')==None and translate:
                    self.tags_collection.update_one({ "name":name},{"$set": {"translate":translate}})
                elif earlier.get('translate') and translate:
                    if translate != earlier.get('translate'):
                        self.tags_collection.update_one({ "name":name},{"$set": {"translate":earlier.get('translate')+','+translate}})
                works_number=earlier.get('works_number')+1
                b=self.tags_collection.update_one({ "name":name},{"$set": {"works_number":works_number}})
            else:
                self.tags_collection.insert_one({'name':name,'works_number':1,'translate':translate})

    def record_info_mongodb(self, ids, collection)->None:
        exists = collection.find({"id": { "$exists": True }},{"_id":0,"id": 1})
        exists_id = [id.get('id') for id in exists]
        '''将图片详情信息保存在mongodb中'''
        for key in list(ids.keys()):
            #插图
            if key == 'illusts' and self.download_type.get('Getillusts'):
                for id in ids.get(key):
                    if int(id) in exists_id:
                        #print(find)
                        #print('已存在,跳过')
                        continue
                    print('获取作品链接...ID:{}'.format(id))
                    info={'type':key}
                    url = 'https://www.pixiv.net/artworks/'+id
                    info.update(self.get_info(url=url,id=id))
                    res = collection.insert_one(info)
                    if res:
                        self.record_in_tags(info.get('tags'))
                        print('成功')
                    if not self.event.is_set():
                        return

            #漫画
            elif key == 'manga' and self.download_type.get('Getmanga'):
                for id in ids.get(key):
                    if int(id) in exists_id:
                        #print('已存在,跳过')
                        continue
                    print('获取作品链接...ID:{}'.format(id))
                    
                    info={'type':key}
                    url = 'https://www.pixiv.net/artworks/'+id
                    info.update(self.get_info(url=url,id=id))
                    res = collection.insert_one(info)
                    if res:
                        self.record_in_tags(info.get('tags'))
                        print('成功')
                    if not self.event.is_set():
                        return

            #漫画系列
            elif key == 'mangaSeries' and self.download_type.get('GetmangaSeries'):
                pass
            #小说系列
            elif key == 'novelSeries' and self.download_type.get('GetnovelSeries'):
                pass
            #小说
            elif key == 'novels' and self.download_type.get('Getnovels'):
                pass

    def mongoDB_auto_backup(self):
        print("开始自动备份,请勿关闭程序!!!")
        names = self.db.list_collection_names()
        now = 1
        all = len(names)
        for name in names:
            collection = self.db[name]
            a = collection.find({"id": { "$exists": True }},{ "_id": 0})
            for docs in a:
                if len(docs)>=9:
                    b = self.backup_collection.find_one({"id":docs.get("id")})
                    if b:continue
                    else:self.backup_collection.insert_one(docs)
            done = int(50 * now / all)
            sys.stdout.write("\r[%s%s] %d%%" % ('█' * done, ' ' * (50 - done), 100 * now / all))
            sys.stdout.flush()
            now += 1
        print("自动备份完成!")
        return True

    def stop_getting(self):
        self.event.clear()
        time.sleep(0.5)
        print('停止获取作者信息')

class Downloader:
    '''
    下载图片(下载小说?->future)
    '''
    def __init__(self, host_path, cookies, download_type, download_number, backup_collection) -> None:
        self.cookies = cookies
        self.host_path = host_path
        self.download_type = download_type
        self.backup_collection = backup_collection
        self.pool = ThreadPoolExecutor(max_workers=download_number)
        self.event = threading.Event()
        self.event.set()

    def start_work_download(self, id):
        '''
        从图片url下载
        '''
        print('开始下载')
        tasks = []
        infogetter = InfoGetter(self.cookies, self.download_type, None, self.backup_collection)
        infos = infogetter.get_info(url='https://www.pixiv.net/artworks/'+id,id=id)
        del infogetter
        urls = infos.get("original_url")
        relative_path = []
        # 检测下载路径是否存在,不存在则创建
        if os.path.isdir(self.host_path+'works/'+id+'/') == False:
            os.makedirs(self.host_path+'works/'+id+'/')
       
        for a in range(len(urls)):
            url = urls[a]
            name = re.search('[0-9]+\_.*',url).group()
            path = self.host_path + 'works/'+id+'/'+name
            relative_path.append('works/'+id+'/'+name)
            # 检测是否已下载
            if not os.path.isfile(path=path):
                info = [id,url,path]
                tasks.append(self.pool.submit(self.download_image, info))

        infos.update({'relative_path':relative_path})
        with open(self.host_path+'works/{}/info.json'.format(id,id),'w',encoding='utf-8') as f:
            json.dump(infos,f,ensure_ascii=False)
        
        for future in  as_completed(tasks):
            if not self.event.is_set():
                return
            future.result()
        self.pool.shutdown()
        print('下载完成')

    def start_tag_download(self):
        '''
        从pixiv获取含标签的图片下载
        '''

    def start_user_download(self):
        '''
        从mongodb中获取图片url并放进线程池
        '''

    def start_following_download(self):
        '''
        从mongodb中获取图片url并放进线程池
        '''
        print('开始下载\n由于需要读取数据库信息并检测是否下载,所以可能等待较长时间')
        tasks = []
        for doc in self.backup_collection.find({"id": { "$exists": True }}):
            if not self.event.is_set():
                return
            if doc.get('failcode'):
                continue
            tasks.clear()
            if not self.download_type.get('Get'+doc.get("type")):
                print("不在下载类型%s中"%self.download_type.get('Get'+doc.get("type")))
                continue
            id = doc.get("id")
            urls = doc.get("original_url")
            uid = doc.get("userId")
            paths = doc.get("relative_path")
            if len(paths) < 1:
                print('数据错误:\n%s'%str(doc))
                continue
            for a in range(len(urls)):
                try:
                    url = urls[a]
                    path = self.host_path + paths[a]
                except:
                    print(doc)
                    continue

                # 检测下载路径是否存在,不存在则创建
                if os.path.isdir(self.host_path+'/picture/'+uid+'/') == False:
                    os.makedirs(self.host_path+'/picture/'+uid+'/')
                # 检测是否已下载
                if not os.path.isfile(path=path):
                    info = [id,url,path]
                    tasks.append(self.pool.submit(self.download_image, info))

            for future in as_completed(tasks):
                if not self.event.is_set():
                    return
                future.result()
        self.pool.shutdown()
        print('下载完成')

    def invalid_image_recorder(self, id, failcode):
        doc = self.backup_collection.find_one_and_update({"id":id},{"$set":{'failcode':failcode}})
        if not doc:
            print('error in record invaild image:'+id+'\n'+doc)

    def stream_download(self, request_info, path):
        """
        流式接收数据并写入文件
        """
        url,headers = request_info
        try:
            response = requests.get(url, headers=headers, cookies=self.cookies, verify=False,proxies=proxie, stream=True)
        except:
            print('下载失败!')
            for a in range(1,4):
                print('自动重试---%d/3'%(a))
                time.sleep(3)
                try:
                    response = requests.get(url, headers=headers, cookies=self.cookies, verify=False, proxies=proxie, stream=True)
                    if response.status_code != 200:
                        print('下载失败!---响应状态码:%d'%response.status_code)
                    f = open(path, 'wb')
                    for chunk in response.iter_content(1024):
                        if not self.event.is_set():
                            f.close()
                            os.remove(path)
                            return
                        f.write(chunk)
                        f.flush()
                    f.close()
                except:
                    print('自动重试失败!')
                    return 1
                    # 错误记录，但感觉没什么用
                    # if a == 3:self.failure_recoder_mongo(id)
        if response.status_code != 200:
            print('下载失败!---响应状态码:%d'%response.status_code)
            return response.status_code
        f = open(path, 'wb')
        for chunk in response.iter_content(1024):
            if not self.event.is_set():
                f.close()
                os.remove(path)
                return
            f.write(chunk)
            f.flush()
        f.close()

    def download_image(self, info):
        '''从队列中获取数据并下载图片'''
        if not self.event.is_set():
            return
        start_time = time.time()    # 程序开始时间
        #print('获取数据%s'%(info))
        id = str(info[0])
        url = info[1]
        path = info[2]
        if re.search('ug',url,re.S) != None:
            info = re.search('img/.*',url).group()
            save_name = id+".zip"
            image_dir = id+"/"
            zip_url = 'https://i.pximg.net/img-zip-ugoira/' + info + 'oira1920x1080.zip'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36','referer': 'https://www.pixiv.net/'}
            print('下载动图ID:%s'%id)
            failcode = self.stream_download((zip_url,headers),save_name)
            if failcode:
                if failcode != 1:
                    self.invalid_image_recorder(int(id), failcode)
                    return
                else:
                    print("[Error]------下载图片%s失败"%id)
                    return
            with zipfile.ZipFile(save_name,'r') as f:
                for file in f.namelist():
                    f.extract(file,image_dir)
            # 删除临时zip文件
            os.remove(save_name)
            # 获取图片路径列表
            image_list = glob.glob(image_dir+"*.jpg")
            # 创建GIF动图对象
            gif_images = [Image.open(image_path) for image_path in image_list]
            # 保存为GIF动图
            with gif_images[0] as first_image:
                first_image.save(path, save_all=True, append_images=gif_images[1:], optimize=False, duration=50, loop=0)
            # 删除解压图片文件夹
            for file_name in os.listdir(image_dir):
                tf = os.path.join(image_dir, file_name)
                os.remove(tf)
            os.rmdir(image_dir)
        else:
            img_url = 'https://www.pixiv.net/artworks/' + id
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36','referer': img_url}
            print('下载图片:ID:%s'%id)
            failcode = self.stream_download((url,headers),path)
            if failcode:
                if failcode != 1:
                    self.invalid_image_recorder(int(id), failcode)
                    return
                else:
                    print("[Error]------下载图片%s失败"%id)
                    return
        if not self.event.is_set():
            return
        end_time = time.time()    # 程序结束时间
        run_time = end_time - start_time    # 程序的运行时间，单位为秒
        if os.path.exists(path):
            print("下载图片{}完成,耗时:{},保存至:{}".format(id,run_time,path))
        else:print('[Error]------图片保存失败')

    def pause_downloading(self):
        pass

    def stop_downloading(self):
        self.event.clear()
        time.sleep(0.5)
        self.pool.shutdown(wait=True, cancel_futures=True)
        print('停止下载')
        return

