#-*-coding:utf-8-*-
from pixiv_tools import *
import threading,json,time,re,os,itertools,sys,webbrowser
from pathlib import Path
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import MessageDialog,Messagebox
from PIL import Image,ImageTk,ImageSequence,UnidentifiedImageError
from concurrent.futures import ThreadPoolExecutor,as_completed

#==================初始化==================

#数据库
import pymongo
client = pymongo.MongoClient('localhost', 27017)
db = client['pixiv']
backup_collection = client["backup"]["backup of pixiv infos"]

# 登录状态验证信息
cookie = ''
#oringal_cookie = 'first_visit_datetime_pc=2023-01-23+00%3A14%3A42; p_ab_id=3; p_ab_id_2=5; p_ab_d_id=969409743; yuid_b=EohWKGY; _gcl_au=1.1.1590819832.1674400503; __utmz=235335808.1674400504.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); PHPSESSID=83945559_gjvPa6Zamm7D9DlhBlOUVzmXDtibWk0h; device_token=a9d02fd82ed56073ee9c405ea9c43b68; privacy_policy_agreement=5; _ga_MZ1NL4PHH0=GS1.1.1674400510.1.1.1674400548.0.0.0; c_type=23; privacy_policy_notification=0; a_type=0; b_type=1; QSI_S_ZN_5hF4My7Ad6VNNAi=v:0:0; login_ever=yes; __utmv=235335808.|2=login%20ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=83945559=1^9=p_ab_id=3=1^10=p_ab_id_2=5=1^11=lang=zh=1; _ga=GA1.1.1220638934.1674400503; __utma=235335808.1220638934.1674400503.1674973853.1674976751.22; __utmc=235335808; __utmt=1; tag_view_ranking=0xsDLqCEW6~qWFESUmfEs~_EOd7bsGyl~Lt-oEicbBr~aKhT3n4RHZ~TqiZfKmSCg~OgLi_QXWK2~gnmsbf1SSR~0jyux9PxkH~SZJe4DVQ3-~LX3_ayvQX4~4TDL3X7bV9~m3EJRa33xU~zIv0cf5VVk~HLTvFcV98c~S0eWMRWoH6~q3eUobDMJW~RTJMXD26Ak~l5mRf3lmn2~BtXd1-LPRH~75zhzbk0bS~TV3I2h_Vd8~tlXeaI4KBb~gzY20gtW1F~WI561SX4pn~jH0uD88V6F~LVSDGaCAdn~ziiAzr_h04~9vxLUp1ZIl~qXzcci65nj~aMSPvw-ONW~OYl5wlor4w~MnGbHeuS94~u8McsBs7WV~Ie2c51_4Sp~39hg5DAst3~ckiinMU_tG~Z-FJ6AMFu8~xha5FQn_XC~Je_lQPk0GY~jhuUT0OJva~PwDMGzD6xn~GCo59yAyB6~SqVgDNdq49~BMGWRnllLS~-vjApZay9I~X8lyQqDJ_c~rpKQpa_qll~R4-PiPeYtW~XyYiM1QdJg~AajMyHII2s~vACH6E5K7c~rIC2oNFqzh~LLyDB5xskQ~IRbM9pb4Zw~U-RInt8VSZ~ef1QMXOaBg~AVueVDbpwj~eVxus64GZU~4QveACRzn3~nK5hU21ePB~DuZWAJi-O1~uW5495Nhg-~MM6RXH_rlN~xjfPXTyrpQ~hrDZxHZLs1~uC2yUZfXDc~LtW-gO6CmS~gCB7z_XWkp~1TeQXqAyHD~GNcgbuT3T-~uRvwDns1lH~b_rY80S-DW~eInvgwdvwj~k3AcsamkCa~erWmq3nmlB~oDcj90OVdf~ti_E1boC1J~NGpDowiVmM~faHcYIP1U0~xVHdz2j0kF~7dpqkQl8TH~f5JQP46dEd~TWrozby2UO~HK5v86l5Tm~CZnOKinv48~SWfYs94Rgz~2kSJBy_FeR~0xRZYD1xTs~liM64qjhwQ~hk4MlvHBiP~W-PCidtmJv~-ErGQUWHGl~cmn1GxZ53u~QM0rfezNVP~XwbsX1-yIW~GX5cZxE2GY~b_G3UDfpN0~bQ1-GzNhfP~ETjPkL0e6r; _ga_75BBYNYN9J=GS1.1.1674976753.21.1.1674976780.0.0.0; __utmb=235335808.4.10.1674976751'

# 保存路径
host_path = 'D:/'
#host_path = 'H:/pixiv/'

# 并发下载进程数
download_number=3

#代理
proxie = ''

version='850f2ba8204f5e6a8a2e36c323bb4ec1a792f255'
#是否开始下载
if_start = {"Start":False}
# 下载的类型
download_type = dict(Getillusts=True,Getmanga=True,GetmangaSeries=False,GetnovelSeries=False,Getnovels=False)
# 设置文件保存路径
config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)),'config.json')

#==========================================
#                   GUI
#==========================================
class Windows():

    def __init__(self) -> None:
        self.tags_collection = db["All Tags"]
        self.following_collection = db["All Followings"]

        self.root = ttk.Window(
            title="图库浏览器",      # 设置窗口的标题
            themename="litera",     # 设置主题
            size=(1400,800),        # 窗口的大小
            position=(200,100),     # 窗口所在的位置
            minsize=(0,0),          # 窗口的最小宽高
            # maxsize=(1920,1080),    # 窗口的最大宽高
            alpha=1.0,              # 设置窗口的透明度(0.0完全透明）
            )
        
        self.root.place_window_center()    #让显现出的窗口居中

        #搜索到的作品数量
        self.work_number = 0
        #搜索到的结果
        self.results = None

        # 加载设置
        self.last_record_time = self.update_config()
        #print(self.last_record_time)

        #========================设置面板========================
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both',expand=True)
        main_window=self.Main_Window(self.root, self.last_record_time)
        self.notebook.add(child= main_window, text="Main")
        search=self.Search(self.root)
        self.notebook.add(child=search, text="Search")
        tag=self.Tag(self.root, search)
        self.notebook.add(child=tag, text="Tag")
        user=self.User(self.root, self.following_collection)
        self.notebook.add(child=user, text="User")
        #config=self.Config(self.root, self.lock)
        config=Config(self.root)
        self.notebook.add(child=config, text="Config")

        #==================循环监听==================
        self.root.protocol('WM_DELETE_WINDOW',self.close_window)
        self.root.mainloop()

    def close_window(self):
        #display = Messagebox.okcancel(message="确认关闭窗口?",alert=True,title="提示")
        #if display == "确定":
            self.root.destroy()
            sys.exit(0)

    def update_config(self=None):
        #========================设置全局变量========================
        global host_path,cookie,download_type,download_number
        with open(config_path,'r',encoding='utf-8') as f:
            json_data = json.load(f)
            # 获取保存路径
            if json_data.get('host_path'):
                host_path = json_data.get('host_path')
            # 获取cookie
            if json_data.get('cookie'):
                cookie = json_data.get('cookie')
            # 下载的作品类型
            if json_data.get('download_type'):
                download_type = json_data.get('download_type')
            # 下载线程数
            if json_data.get('download_number'):
                download_number = json_data.get('download_number')
            last_record_time = json_data.get('last_record_time')
        
        return last_record_time

    class Main_Window(ttk.Frame):
        
        def __init__(self,root,time):
            super().__init__(root)
            self.last_record_time = time
            self.user_input = ttk.StringVar(master=self)
            self.user_input.set('输入搜索的标签或作者id(使用英文逗号分隔!!!)')
            self.input_entry = ttk.Entry(master=self,width=100,textvariable=self.user_input)
            self.input_entry.grid(column=0, row=0, columnspan=4)

            self.download_method = ttk.StringVar()
            self.download_method.set(3)
            self.download_method_dist = {
                "0":"work",
                "1":"tag",
                "2":"user",
                "3":"following"
            }
            ttk.Radiobutton(self, text='下载该ID的作品(仅下载!!!)', variable=self.download_method, value=0).grid(column=0, row=1)
            ttk.Radiobutton(self, text='下载含该标签的作品(未启用)', variable=self.download_method, value=1).grid(column=1, row=1)
            ttk.Radiobutton(self, text='下载该UID的作者的作品(未启用)\n既然都要下作者的全部作品了\n为什么不直接关注呢?', variable=self.download_method, value=2).grid(column=2, row=1)
            ttk.Radiobutton(self, text='下载关注的作者的作品', variable=self.download_method, value=3).grid(column=3, row=1)
            self.download_button = ttk.Button(master=self,width=8,text='开始下载',command=self.start_download)
            self.download_button.grid(column=4, row=0)
            #self.download_progressbars = {}
            if len(cookie) < 10:
                print(cookie)
                exit(0)
            """进度条------摆烂
            for a in range(0,download_number):
                #download_progress = ttk.Progressbar(self, length=500, mode='indeterminate', maximum=500, value= 100)
                download_progress = ttk.Floodgauge(self, length=500, maximum=500, mode='determinate', text='Downloading...0%')
                download_progress.pack(side='top')
                self.download_progressbars.update({a:download_progress})
            """

        def start_download(self):
            download_method = self.download_method_dist[self.download_method.get()]
            if download_method == 'work':
                self.download_button.config(default='disabled')
                downloader = Downloader(host_path, cookie, download_type, download_number, backup_collection)
                downloader.start_work_download(id=self.user_input.get())
                self.download_button.config(default='normal')
            elif download_method == 'following':
                followings_recorder = FollowingsRecorder(cookie,db)
                #followings_recorder = FollowingsRecorder(cookie,client['Test'])
                followings_recorder.following_recorder()
                del followings_recorder
                #global input_infos
                #self.t = threading.Thread(target=self.get.download,name='download_manger',args=(getinfo,),daemon=True)
                self.t = threading.Thread(target=self.threading_manger,name='threading_manger',daemon=True)
                self.t.start()
                self.download_button.config(text='停止下载',command=self.stop_download,default='normal')

        def stop_download(self):
            """
            if self.t.is_alive():
                print('等待图片下载完毕......请勿关闭程序!!!')
            """
            try:self.info_getter.stop_getting()
            except AttributeError:pass    
            try:self.downloader.stop_downloading()
            except AttributeError:pass    
            try:del self.info_getter
            except AttributeError:pass
            try:del self.downloader
            except AttributeError:pass
            self.download_button.config(text='开始下载',command=self.start_download)

        def threading_manger(self):
            newtime = time.strftime("%Y%m%d%H%M%S")
            if Tools.compare_datetime(lasttime=str(self.last_record_time), newtime=newtime):
                self.info_getter = InfoGetter(cookie, download_type, db, backup_collection)
                success = self.info_getter.start_get_info()
                if success:
                    with open(config_path,'r',encoding='utf-8') as f:
                        json_data = json.load(f)
                        json_data.update({"last_record_time":newtime})
                    with open(config_path,'w',encoding='utf-8') as f:
                        json.dump(json_data,f,ensure_ascii=False)
            self.downloader = Downloader(host_path, cookie, download_type, download_number, backup_collection)
            self.downloader.start_following_download()
            self.download_button.config(text='开始下载',command=self.start_download)

        """
        def refresh_progressbar(self, index, done):
            download_progress = self.download_progressbars.get(index)
            download_progress.configure(text='Downloading...{}%'.format(done), value = 5*done)
        """

    class Search(ttk.Frame):

        def __init__(self, root):
            super().__init__(master=root)
            self.pack()
            self.all = []
            self.setupUI()

        def setupUI(self):
            #------------------信息显示布局------------------
            self.info_entry_frame = ttk.Frame(self)
            #获取输入信息
            self.search_txt = ttk.StringVar(self.info_entry_frame)
            self.search_txt.set('输入搜索的标签或作者id')
            self.search_entry = ttk.Entry(master=self.info_entry_frame,width=30,font=("微软雅黑", 10),
                                        justify='left',textvariable=self.search_txt)
            self.search_entry.grid(column=0,row=0,columnspan=3)
            self.search_button = ttk.Button(master=self.info_entry_frame,width=5,text='搜索',command=self.search)
            self.search_button.grid(column=3,row=0,columnspan=1)

            # 打开图片网页
            self.img_url = "https://www.pixiv.net/"
            self.open_in_webdrive_button = ttk.Button(master=self.info_entry_frame,width=40,text='在浏览器中打开',command=self.open_in_web)
            self.open_in_webdrive_button.grid(column=0,row=1,columnspan=4)
            # 打开资源管理器
            self.img_path = host_path+"picture/"
            self.open_in_windows_button = ttk.Button(master=self.info_entry_frame,width=40,text='在windows资源管理器中打开',command=self.open_in_windows)
            self.open_in_windows_button.grid(column=0,row=2,columnspan=4)

            #self.picture_info = ttk.Text(self.info_entry_frame,font=("微软雅黑", 10),width=40,height=20)
            self.picture_info = ttk.ScrolledText(self.info_entry_frame,font=("微软雅黑", 10),width=35,height=20)
            self.picture_info.insert('0.0','单击图片获取图片信息\n双击图片查看原图(未启用)')
            self.picture_info.configure(state = 'disabled')
            self.picture_info.grid(column=0,row=3,columnspan=4)
            self.info_entry_frame.grid(row=0, column=0, rowspan= 6, columnspan=4)

            #------------------图片显示布局------------------
            self.img_width = 240                    # 图片宽度
            self.img_height = 320                   # 图片高度
            self.rows = 2                           # 图片行数
            self.columns = 4                        # 图片列数
            self.pagesize=self.rows*self.columns    # 每页显示的数量
            self.page=1                             # 页数
            self.total_page = 1                       # 总页数
            #self.images = []                        # 处理好的图片列表
            self.images = {}                        # 处理好的图片字典
            self.image_frame = ttk.Frame(self,width=self.img_width*self.columns,height=self.img_height*self.rows)
            self.set_page = ttk.IntVar()
            self.set_page.set(self.page)

            # 创建显示图片的画布列表
            self.img_canvas = []
            for i in range(self.rows):
                for j in range(self.columns):
                    self.img_canvas.append(ttk.Canvas(self.image_frame,width=self.img_width,height=self.img_height,bd=2,relief='groove'))
                    self.img_canvas[i*self.columns+j].create_text(self.img_width/2,self.img_height/2,text='搜索后自动显示图片')
                    self.img_canvas[i*self.columns+j].grid(row=i, column=j, rowspan=1, columnspan=1, padx=1, pady=1)

            #------------------页码显示布局------------------
            self.page_frame = ttk.Frame(self,width=self.img_width*self.columns)
            self.prev_page_button = ttk.Button(self.page_frame, text='prev', command=self.prev_page, width=10)
            self.prev_page_button.grid(row=0, column=0)

            self.page_label = ttk.Label(self.page_frame, text=str(self.page)+'/'+str(self.total_page), width=10)
            self.page_label.grid(row=0, column=1)

            self.choose_page_entry = ttk.Entry(self.page_frame, textvariable=self.set_page, width=10)
            self.choose_page_entry.grid(row=0, column=2)

            self.choose_page_button = ttk.Button(self.page_frame, text='jump', command=self.choose_page, width=10)
            self.choose_page_button.grid(row=0, column=3)

            self.next_page_button = ttk.Button(self.page_frame, text='next', command=self.next_page, width=10)
            self.next_page_button.grid(row=0, column=4)

            self.image_frame.grid(row=0, column=5, rowspan=4, columnspan=4)
            self.page_frame.grid(row=5, column=5, rowspan=1, columnspan=4)

            #------------------创建事件绑定------------------
            for index in range(self.pagesize):
                self.img_canvas[index].bind("<Button-1>", self.show_image_info)
                #self.img_labels[index].bind("<Double-Button-1>", lambda event:self.Show_Detial_Image(self, 
                #                                    self.img_labels, self.all, self.page, self.pagesize, event))

        def set_search_info(self,info):
            txt = self.search_txt.get()
            if txt and txt!="输入搜索的标签或作者id":
                self.search_txt.set(txt+","+info)
            else:self.search_txt.set(info)

        def search(self):
            self.all.clear()
            self.work_number = 0
            self.page = 1
            self.total_page = 1
            search_info = self.search_txt.get()
            self.results = None
            collection = client['backup']['backup of pixiv infos']
            if re.findall("\+",search_info):
                and_search = []
                for one_search in search_info.split("+"):
                    if re.search("\d{4,}",one_search):
                        and_search.append({"userId":one_search})
                    else:and_search.append({'tags.'+one_search:{'$exists': 'true'}})
                self.results = collection.find({"$and":and_search}).sort("id",-1)
                #self.results = collection.find({"$and":and_search})
                #self.work_number = collection.find({"$and":and_search})
                
            elif re.findall("\,",search_info):
                or_search = []
                for one_search in search_info.split(","):
                    if re.search("\d{4,}",one_search):
                        or_search.append({"userId":one_search})
                    else:or_search.append({'tags.'+one_search:{'$exists': 'true'}})
                    self.results = collection.find({"$or":or_search}).sort("id",-1)
                    #self.results = collection.find({"$or":or_search})
            
            else:
                one_search ={}
                if re.search("\d{4,}",search_info):
                    one_search.update({"userId":search_info})
                else:one_search.update({'tags.'+search_info:{'$exists': 'true'}})
                self.results = collection.find(one_search).sort("id",-1)
                #self.results = collection.find(one_search)

            for row in self.results:
                self.all.append(row)
                self.work_number += 1
                #print(row.get("id"))
            self.total_page = (self.work_number - 1) // (self.rows * self.columns) + 1
            #print("总页数:%d"%(self.total_page))
            """
            #self.page_number = len(self.work_ids)//self.pagesize
            #if len(self.work_ids)%self.pagesize !=0:
            #    self.page_number+=1
            self.page_number = self.work_number//self.pagesize
            if self.work_number%self.pagesize !=0:
                self.page_number+=1
            print(self.page_number)
            """
            #self.initialize_img_new()
            self.page = 1
            self.show_page()

        def open_in_web(self):
            webbrowser.open(self.img_url, new=0, autoraise=True) 

        def open_in_windows(self):
            file = host_path+self.img_path
            file = os.path.realpath(file)
            print(file)
            if os.path.exists(file):
                os.system(f'explorer /select, {file}')
            else:
                print("文件不存在:%s"%(file))

        def show_image_info(self,event):
            for index in range(self.pagesize):
                if event.widget == self.img_canvas[index]:
                    try:
                        result = self.all[(self.page-1)*self.pagesize:self.page*self.pagesize][index]
                    except IndexError:pass
                    id = result.get("id")
                    type = result.get("type")
                    title = result.get("title")
                    userid = result.get("userId")
                    username = result.get("username")
                    description = result.get("description")
                    self.img_url = "https://www.pixiv.net/artworks/"+str(id)
                    self.img_path = result.get("relative_path")[0]

            infos = "ID:{}\nType:{}\nTitle:{}\nUserID:{}\nUserName:{}\nDescription:\n{}"
            infos = infos.format(id, type, title, userid, username, description)
            #print(infos)
            self.picture_info.configure(state='normal')
            self.picture_info.delete('0.0','end')
            self.picture_info.insert('0.0',infos)
            self.picture_info.configure(state='disabled')

        def initialize_img(self):
            self.images.clear()
            self.loaded_images = {}
            paths = {}
            images = self.all[(self.page-1)*self.pagesize:self.page*self.pagesize]
            for index in range(len(images)):
                try:
                    img = host_path + images[index].get("relative_path")[0]
                except IndexError:print(images)
                if re.search("\.gif",img):
                    self.loaded_images.update({index:"gif"})
                else:
                    if os.path.exists(img):
                        paths.update({index:img})
                    else:
                        self.loaded_images.update({index:None})
            #print(self.loaded_images)
            loaded_images=Windows.image_loader(paths, self.img_width, self.img_height)
            self.loaded_images.update(loaded_images)
            #print(self.loaded_images)
            
            for index in range(len(images)):
                img = self.loaded_images.get(index)
                self.images.append(img)
            
            #print(self.images)

        def initialize_img_new(self):
            self.images.clear()
            self.loaded_images = {}
            paths = {}
            images = self.all[(self.page-1)*self.pagesize:self.page*self.pagesize]
            
            def image_loader_new(index, path)->dict:
                """
                功能：读取图片并缩放，处理为imagetk形式\n
                path->图片的路径及其索引\n
                load_image->使用PIL加载图片，若格式损坏则删除\n
                return->处理完的图片，包含索引和对应数据
                """
                def resize_image(image):
                    """
                    将图片等比例缩放
                    """
                    # Get image's original width and height
                    original_width, original_height = image.size

                    # Calculate the new width and height based on the original aspect ratio and the maximum width and height
                    aspect_ratio = original_width / original_height
                    if aspect_ratio > 1:
                        new_width = min(original_width, self.img_width)
                        new_height = int(new_width / aspect_ratio)
                    else:
                        new_height = min(original_height, self.img_height)
                        new_width = int(new_height * aspect_ratio)

                    # Resize the image and create an ImageTk object
                    resized_image = image.resize((new_width, new_height))

                    image_tk = ImageTk.PhotoImage(resized_image)

                    return image_tk
                
                try:
                    loaded_image = Image.open(path)
                except UnidentifiedImageError:
                    os.remove(path)
                try:
                    loaded_image.load()
                except OSError:
                    loaded_image.close()
                    os.remove(path)
                    return {index:None}
                image=resize_image(loaded_image)
                
                return {index:image}
            
            for index in range(len(images)):
                try:
                    img = host_path + images[index].get("relative_path")[0]
                except IndexError:print(images)
                if re.search("\.gif",img):
                    self.loaded_images.update({index:"gif"})
                else:
                    if os.path.exists(img):
                        paths.update({index:img})
                    else:
                        self.loaded_images.update({index:None})
        
            def get_result(future):
                self.loaded_images.update(future.result())
            
            with ThreadPoolExecutor(6) as executor: # 创建线程池
                future_list = [executor.submit(image_loader_new, index, path) for index,path in paths.items()] # 提交任务
            
            for future in as_completed(future_list):
                future.add_done_callback(get_result)

            for index in range(len(images)):
                img = self.loaded_images.get(index)
                self.images.append(img)
            
            #print(self.images)

        def show_img(self,index:int):
            
            def resize_image(image):
                """将图片等比例缩放"""

            def image_loader_new(path)->dict:
                """
                功能：读取图片并缩放，处理为imagetk形式\n
                path->图片的路径及其索引\n
                load_image->使用PIL加载图片，若格式损坏则删除\n
                return->处理完的图片，包含索引和对应数据
                """
            self.img_canvas[index].delete("all")
            images = self.all[(self.page-1)*self.pagesize:self.page*self.pagesize]
            try:
                path = host_path + images[index].get("relative_path")[0]
            except IndexError:print(images)
            if re.search("\.gif",path):
                #self.images.update({index:'gif'})
                self.img_canvas[index].create_text(0, 0, text = "This is a gif,double click\nleft mouse button if you want see it", anchor='nw')
            else:
                if os.path.exists(path):
                    try:loaded_image = Image.open(path)
                    except UnidentifiedImageError:os.remove(path)
                    if loaded_image:
                        original_width, original_height = loaded_image.size
                        aspect_ratio = original_width / original_height
                        if aspect_ratio > 1:
                            new_width = min(original_width, self.img_width)
                            new_height = int(new_width / aspect_ratio)
                        else:
                            new_height = min(original_height, self.img_height)
                            new_width = int(new_height * aspect_ratio)
                        resized_image = loaded_image.resize((new_width, new_height))
                        self.images.update({index:ImageTk.PhotoImage(resized_image)})
                        self.img_canvas[index].create_image(0, 0, image=self.images[index], anchor='nw')
                    else:
                        self.img_canvas[index].create_text(0, 0, text = "未下载图片或移动了图片", anchor='nw')
                else:
                    self.img_canvas[index].create_text(0, 0, text = "未下载图片或移动了图片", anchor='nw')

        def show_page(self):
            self.images.clear()
            for i in range(self.rows):
                for j in range(self.columns):
                    index = i*self.columns+j
                    self.show_img(index)
                    '''以前的方法
                    if index < len(self.images):
                        #self.img_labels[index].config(image=self.images[index])
                        image=self.images[index]
                        self.img_labels[index].delete("all")
                        if image:
                            if image == "gif":
                                self.img_labels[index].create_text(0, 0, text = "This is a gif,double click\nleft mouse button if you want see it", anchor='nw')
                            else:
                                self.img_labels[index].create_image(0, 0, image=image, anchor='nw')
                        else:self.img_labels[index].create_text(0, 0, text = "未下载图片或移动了图片", anchor='nw')
                    else:
                        self.img_labels[index].delete("all")
                        #print(index)
                        #self.img_labels[index].config(image=None)
                    '''
            self.page_label.config(text=str(self.page)+'/'+str(self.total_page))

        def prev_page(self):
            if self.page - 1 < 1:
                return
            else:
                self.page -= 1
                #self.initialize_img()
                self.show_page()

        def next_page(self):
            if self.page + 1 > self.total_page:
                return
            else:
                self.page += 1
                #self.initialize_img()
                self.show_page()

        def choose_page(self):
            if self.set_page.get() > self.total_page:
                self.set_page.set(self.page)
                return
            elif self.set_page.get() < 1:
                self.set_page.set(self.page)
                return
            else:
                self.page = self.set_page.get()
                #self.initialize_img()
                self.show_page()

        def show_detial_image(self, img_labels, all_img, page, pagesize, event):
            
            detial_imgs = []
            index = 0
            # 处理图片
            for index in range(pagesize):
                if event.widget == img_labels[index]:
                    result = all_img[(page-1)*pagesize:page*pagesize][index]
                    paths = result.get("relative_path")
                    for path in paths:
                        path = host_path + path
                        if os.path.exists(path):
                        #    detial_imgs.append(Image.open(path))
                            os.system('start {file}'.format(file=path))
                        else:
                            pass
            for img in detial_imgs:
                img.show()
                break
            """
            file = host_path+self.img_path
            file = os.path.realpath(file)
            print(file)
            if os.path.exists(file):
                os.system('start {file}'.format(file=file))
            else:
                print("文件不存在:%s"%(file))
            """


            class AnimatedGif(ttk.Frame):
                def __init__(self, master, path, width, height):
                    super().__init__(master, width=width, height=height)

                    self.img_width = width
                    self.img_height = height
                    #self.img_container = ttk.Label(self, image=next(self.image_cycle))
                    self.img_container = ttk.Canvas(self, width=width, height=height)
                    self.img_container.pack() 
                    # open the GIF and create a cycle iterator
                    if not os.path.exists(path):
                        self.img_container.create_text(width/2, height/2, text = "未下载动图或移动了动图", anchor='nw')
                        return
                    file_path = Path(__file__).parent / path
                    with Image.open(file_path) as im:
                        # create a sequence and resize images
                        sequence = ImageSequence.Iterator(im)
                        images = self.resize_images(sequence)
                        self.image_cycle = itertools.cycle(images)

                        # length of each frame
                        self.framerate = im.info["duration"]
                    
                    self.img_container.create_image(0, 0, image=next(self.image_cycle), anchor='nw') 
                    self.after(self.framerate, self.next_frame)

                def next_frame(self):
                    """Update the image for each frame"""
                    #self.img_container.configure(image=next(self.image_cycle))
                    self.img_container.delete("all")
                    self.img_container.create_image(0, 0, image=next(self.image_cycle), anchor='nw') 
                    self.after(self.framerate, self.next_frame)

                def resize_images(self,images):
                    max_image_width = 0
                    max_image_height = 0
                    resized_images = []
                    for image in images:
                        # Get image's original width and height
                        original_width, original_height = image.size

                        # Calculate the new width and height based on the original aspect ratio and the maximum width and height
                        aspect_ratio = original_width / original_height
                        if aspect_ratio > 1:
                            new_width = min(original_width, self.img_width)
                            new_height = int(new_width / aspect_ratio)
                        else:
                            new_height = min(original_height, self.img_height)
                            new_width = int(new_height * aspect_ratio)

                        # Resize the image and create an ImageTk object
                        resized_image = image.resize((new_width, new_height))
                        image_tk = ImageTk.PhotoImage(resized_image)
                        resized_images.append(image_tk)

                        # Update the maximum image width and height
                        max_image_width = max(max_image_width, new_width)
                        max_image_height = max(max_image_height, new_height)
                    return resized_images   

    class User(ttk.Frame):

        def __init__(self, root, following_collection):
            super().__init__(root)
            self.all_users = []
            self.images = {}
            #self.pack()
            self.following_collection = following_collection
            '''
            #check if 作者缩略图 is exist
            if not os.path.exists("./作者缩略图"):
                os.mkdir("./作者缩略图")
            '''
            for one in self.following_collection.find({"userId":{'$exists': 'true'}},{ "_id": 0}):
                self.all_users.append(one)
            self.setupUI()
            self.user_info()
        
        def setupUI(self):
            self.img_width = 160                    # 图片宽度
            self.img_height = 160                   # 图片高度
            self.img_number = 4                     # 图片个数
            self.user_number = 4                    # 作者个数
            self.page=1                             # 页数
            #===============================优化===============================
            self.all_page = len(self.all_users)//self.user_number+1                     # 总页数
            #print(self.all_page)
            #==============================================================
            self.set_page = ttk.IntVar()
            self.set_page.set(self.page)
            self.user_frames = {}
            self.user_texts = {}
            #self.img_canvas = {}

            # 创建显示列表
            for i in range(self.user_number):
                user_frame = ttk.Frame(self, width=40+(self.img_width*self.img_number), height=self.img_height)
                img_canvas = []
                #user_text = ttk.Text(self, width=40, height=8)
                user_text = ttk.Text(user_frame, width=40, height=8)
                #user_text.grid(column=0,row=i)
                user_text.pack(side='left')
                self.user_texts.update({i:user_text})
                for j in range(self.img_number):
                    #img_canva.append(ttk.Canvas(self,width=self.img_width,height=self.img_height,bd=2,relief='groove'))
                    #img_canva[j].grid(column=1+j,row=i)
                    img_canvas.append(ttk.Canvas(user_frame,width=self.img_width,height=self.img_height,bd=2,relief='groove'))
                    img_canvas[j].pack(side='left')
                #self.img_canvas.update({i:img_canva})
                #user_frame.pack(side='top')
                user_frame.grid(column=0,row=i,columnspan=4)
                self.user_frames.update({i:{'user_text':user_text, 'img_canvas':img_canvas}})

            self.prev_page_button = ttk.Button(self, text='prev', command=self.prev_page)
            self.prev_page_button.grid(row=self.user_number+1, column=0)

            self.choose_page_entry = ttk.Entry(self, textvariable=self.set_page)
            self.choose_page_entry.grid(row=self.user_number+1, column=1)

            self.choose_page_button = ttk.Button(self, text='jump', command=self.choose_page)
            self.choose_page_button.grid(row=self.user_number+1, column=2)

            self.next_page_button = ttk.Button(self, text='next', command=self.next_page)
            self.next_page_button.grid(row=self.user_number+1, column=3)


            #------------------创建事件绑定------------------
            #for index in len(self.all_users):
                #self.img_labels[index].bind("<Button-1>", self.show_image_info)

        def user_info(self):
            if len(self.all_users)>=4:
                user_infos = self.all_users[(self.page-1)*4:self.page*4]
            else:user_infos = self.all_users
            for i in range(len(user_infos)):
                user_info = user_infos[i]
                #user_text = self.user_texts.get(i)
                user_text = self.user_frames.get(i).get('user_text')
                user_text.configure(state='normal')
                info = "userName:{}\nuserId:{}\nuserComment:{}".format(user_info['userName'], user_info['userId'], user_info.get('userComment'))
                user_text.delete(0.0, "end")
                user_text.insert(0.0, info)
                user_text.configure(state='disable')
                #self.images.update({i:self.initialize_img(user_info['userId'])})
                self.images.update({i:self.initialize_img(user_info['userName'])})
                #print(self.images)
            for i in range(len(user_infos)):
                for j in range(4):
                    #self.img_canvas.get(i)[j].delete(0.0, "end")
                    self.user_frames.get(i).get('img_canvas')[j].delete(0.0, "end")
                    try:
                        #self.img_canvas.get(i)[j].create_image(0, 0, image=self.images[i][j], anchor='nw')
                        self.user_frames.get(i).get('img_canvas')[j].create_image(0, 0, image=self.images[i][j], anchor='nw')
                    except IndexError:pass

        def initialize_img(self,userName):
            paths = {}
            images = []
            """
            for a in range(self.img_number):
                path = "./作者缩略图/{}_{}".format(usreId,a)
                if os.path.exists(path):
                    paths.append(path)
                else:paths.append(None)
            
            for root, dirs, files in os.walk(host_path+"/picture/{}/".format(usreId)):
                files.sort()
                files = files[0:self.img_number]
                for a in range(0,len(files)):
                    path = os.path.join(root, files[a])
                    if paths[a]:
                        images.append(ImageTk.PhotoImage(resize(Image.open(path))))
                    else:
                        image = resize(Image.open(path))
                        image.save("./作者缩略图/{}".format(usreId)+"_{}.png".format(a))
                        images.append(ImageTk.PhotoImage(image))
            """
            collection = db[userName]
            a=0
            for one in collection.find({"id":{'$exists': 'true'}},{ "_id": 0,"relative_path":1}).sort("id",-1):
                if a==4:
                    break
                path=host_path+one.get('relative_path')[0]
                #print(path)
                if os.path.exists(path):
                    #images.append(Windows.resize_image(Image.open(path), 160, 120))
                    paths.update({a:path})
                    a+=1
            loaded_images=Windows.image_loader(paths, self.img_width, self.img_height)
            for a in range(len(loaded_images)):
                images.append(loaded_images.get(a))
            return images

        def prev_page(self):
            if self.page - 1 < 1:
                return
            else:
                self.page -= 1
                self.set_page.set(self.page)
                self.user_info()

        def next_page(self):
            if self.page + 1 > self.all_page:
                return
            else:
                self.page += 1
                self.set_page.set(self.page)
                self.user_info()

        def choose_page(self):
            if self.set_page.get() > self.all_page:
                self.set_page.set(self.page)
                return
            elif self.set_page.get() < 1:
                self.set_page.set(self.page)
                return
            else:
                self.page = self.set_page.get()
                self.user_info()

    class Tag(ttk.Frame):

        def __init__(self, root, search):
            super().__init__(root)
            self.tags_collection = db['All Tags']
            self.like_tag_collection = db['Like Tag']
            self.dislike_tag_collection = db['Dislike Tag']
            self.pack()
            self.setupUI()
            self.search = search

            #================set treeview=================

            # 所有标签
            self.all_tags=self.load_tags(search_type='all')
            #print(self.all_tags)
            #return
            for row in self.all_tags:
                self.all_tags_treeview.insert('', 'end', values=row)
            # print(tv.get_children())#('I001', 'I002', 'I003', 'I004', 'I005')
            self.all_tags_treeview.selection_set('I001')
            self.all_tags_treeview.heading(0, text='Name')
            self.all_tags_treeview.heading(1, text='Translatation')
            self.all_tags_treeview.column(0, width=200)
            self.all_tags_treeview.column(1, width=200, anchor='center')
            # 喜欢的标签
            for row in self.load_tags(search_type='like'):
                self.like_tags.insert('', 'end', values=row)
            self.like_tags.selection_set('I001')
            self.like_tags.heading(0, text='Name')
            self.like_tags.heading(1, text='Translatation')
            self.like_tags.column(0, width=200)
            self.like_tags.column(1, width=200, anchor='center')
            # 不喜欢的标签
            for row in self.load_tags(search_type='dislike'):
                self.dislike_tags.insert('', 'end', values=row)
            self.dislike_tags.selection_set('I001')
            self.dislike_tags.heading(0, text='Name')
            self.dislike_tags.heading(1, text='Translatation')
            self.dislike_tags.column(0, width=200)
            self.dislike_tags.column(1, width=200, anchor='center')

        def setupUI(self):
            # initialize treeview
            #self.all_tag_scroll = ttk.ScrolledText(self.all_tag_frame,padding=5, height=10, autohide=True)
            self.quary = ttk.StringVar(self)
            self.search_tag_entry = ttk.Entry(master=self,width=90,textvariable=self.quary)
            self.search_tag_entry.grid(column=0,row=0,columnspan=2)
            self.quary.set('输入要搜索的标签')
            self.search_tag_button = ttk.Button(master=self,width=20,text='search',command=self.finder)
            self.search_tag_button.grid(column=2,row=0,columnspan=1)

            self.all_tag_frame = ttk.Frame(self)
            ttk.Label(self.all_tag_frame, text='All Tags', width=45).grid(column=0, row=0, columnspan=4)
            self.all_tags_treeview = ttk.Treeview(master=self.all_tag_frame, columns=[0, 1], show='headings', height=30)
            self.all_tags_treeview.grid(column=0, row=1, columnspan=3, sticky='w')
            self.all_tag_scroll = ttk.Scrollbar(self.all_tag_frame,command=self.all_tags_treeview.yview)
            self.all_tags_treeview.config(yscrollcommand=self.all_tag_scroll.set)
            self.all_tag_scroll.grid(column=3,row=1,sticky='ns')
            ttk.Button(self.all_tag_frame,text='selcect',
                       command=lambda:self.selcect('all'),width=13).grid(column=0, row=2, sticky='w')
            ttk.Button(self.all_tag_frame,text='like',
                       command=lambda:self.sendlike(self.all_tags_treeview),width=13).grid(column=1,row=2, sticky='w')
            ttk.Button(self.all_tag_frame,text='dislike',
                       command=lambda:self.senddislike(self.all_tags_treeview),width=13).grid(column=2, row=2, sticky='w', columnspan=2)
            self.all_tag_frame.grid(column=0,row=1)

            self.like_tag_frame = ttk.Frame(self)
            ttk.Label(self.like_tag_frame, text='Like Tags', width=45).grid(column=0, row=0, columnspan=3)
            self.like_tags = ttk.Treeview(master=self.like_tag_frame, columns=[0, 1], show='headings', height=30)
            self.like_tags.grid(column=0, row=1, columnspan=2, sticky='w')
            self.like_tag_scroll = ttk.Scrollbar(self.like_tag_frame,command=self.like_tags.yview)
            self.like_tags.config(yscrollcommand=self.like_tag_scroll.set)
            self.like_tag_scroll.grid(column=2, row=1,sticky='ns')
            ttk.Button(self.like_tag_frame,text='selcect',
                       command=lambda:self.selcect('like'),width=21).grid(column=0,row=2, sticky='w')
            ttk.Button(self.like_tag_frame,text='delete',
                       command=lambda:self.delete('like'),width=21).grid(column=1, row=2, sticky='w', columnspan=2)
            self.like_tag_frame.grid(column=1,row=1)

            self.dislike_tag_frame = ttk.Frame(self)
            ttk.Label(self.dislike_tag_frame, text='Dislike Tags', width=45).grid(column=0, row=0, columnspan=4)
            self.dislike_tags = ttk.Treeview(master=self.dislike_tag_frame, columns=[0, 1], show='headings', height=30)
            self.dislike_tags.grid(column=0, row=1, columnspan=3, sticky='w')
            self.dislike_tag_scroll = ttk.Scrollbar(self.dislike_tag_frame,command=self.dislike_tags.yview)
            self.dislike_tags.config(yscrollcommand=self.dislike_tag_scroll.set)
            self.dislike_tag_scroll.grid(column=3, row=1,sticky='ns')
            ttk.Button(self.dislike_tag_frame,text='selcect',
                       command=lambda:self.selcect('dislike'),width=21).grid(column=0,row=2, sticky='w')
            ttk.Button(self.dislike_tag_frame,text='delete',
                       command=lambda:self.delete('dislike'),width=21).grid(column=1, row=2, sticky='w', columnspan=2)
            self.dislike_tag_frame.grid(column=2,row=1)

        def load_tags(self, search_type=['all','like','dislike'])->list:
            if search_type == 'all':
                tags = self.tags_collection.find({"works_number": {"$gt": 5}},{ "_id": 0}).sort("works_number",-1).limit(500)
            elif search_type == 'like':
                tags = self.like_tag_collection.find({"name":{'$exists': 'true'}},{ "_id": 0})
            elif search_type == 'dislike':
                tags = self.dislike_tag_collection.find({"name":{'$exists': 'true'}},{ "_id": 0})
            table_data = []
            for tag in tags:
                #if tag.get("translate"):
                table_data.append((tag.get("name"),tag.get("translate")))
            return table_data

        def selcect(self,tree_type=['all','like','dislike']):
            if tree_type=='all':
                tree=self.all_tags_treeview
            elif tree_type=='like':
                tree=self.like_tags
            elif tree_type=='deslike':
                tree=self.dislike_tags
            selection = tree.selection()[0]
            print(selection)
            selection = tree.item(selection).get('values')
            print(selection)
            self.search.set_search_info(info=selection[0])

        def delete(self,tree_type=['like','dislike']):
            if tree_type=='like':
                tree=self.like_tags
                collection=self.like_tag_collection
            elif tree_type=='dislike':
                tree=self.dislike_tags
                collection=self.dislike_tag_collection
            selections = tree.selection()
            selection = tree.item(selections).get('values')
            for item in selections:
                tree.delete(item)
            name,a = selection
            collection.find_one_and_delete({'name':name})

        def sendlike(self,tree):
            selection = tree.selection()[0]
            selection = tree.item(selection).get('values')
            selection = (selection[0],selection[1])
            earlier = self.like_tag_collection.find_one({'name':selection[0]})
            if earlier:
                if earlier != {'name':selection[0], 'translate':selection[1]}:
                    self.like_tag_collection.find_one_and_update({'name':selection[0]}, {"$set":{'translate':selection[1]}})
            else:
                self.like_tag_collection.insert_one({'name':selection[0], 'translate':selection[1]})
                self.like_tags.insert('','end',values=selection)
            self.like_tags.update()

        def senddislike(self,tree):
            selection = tree.selection()[0]
            selection = tree.item(selection).get('values')
            selection = (selection[0],selection[1])
            earlier = self.dislike_tag_collection.find_one({'name':selection[0]})
            if earlier:
                if earlier != {'name':selection[0], 'translate':selection[1]}:
                    self.dislike_tag_collection.find_one_and_update({'name':selection[0]}, {"$set":{'translate':selection[1]}})
            else:
                self.dislike_tag_collection.insert_one({'name':selection[0], 'translate':selection[1]})
                self.dislike_tags.insert('','end',values=selection)
            self.dislike_tags.update()

        def finder(self):

            def fuzzy_finder(key, data):
                """
                模糊查找器
                :param key: 关键字
                :param data: 数据
                :return: list
                """
                # 结果列表
                suggestions = []
                # 非贪婪匹配，转换 'djm' 为 'd.*?j.*?m'
                # pattern = '.*?'.join(key)
                pattern = '.*%s.*'%(key)
                # print("pattern",pattern)
                # 编译正则表达式
                regex = re.compile(pattern)
                for item in data:
                    # 检查当前项是否与regex匹配。
                    match = regex.search(str(item))
                    if match:
                        # 如果匹配，就添加到列表中
                        suggestions.append(item)

                return suggestions
            
            result_list = []
            for one in self.quary.get():
                result_list = list(set(result_list) | set(fuzzy_finder(one,self.all_tags)))
            print(result_list)

    def image_loader(paths, img_width, img_height)->dict:
        """
        功能：读取图片并缩放，处理为imagetk形式\n
        paths->图片的路径及其索引\n
        load_image->使用PIL加载图片，若格式损坏则删除\n
        return->处理完的图片，包含索引和对应数据
        """
        #print(paths)
        loaded_images = {}
        def load_image(index, path):
            try:
                loaded_image = Image.open(path)
            except UnidentifiedImageError:
                os.remove(path)
            try:
                loaded_image.load()
            except OSError:
                loaded_image.close()
                os.remove(path)
                return {index:None}
            return {index:loaded_image}
        
        def get_result(future):
            #print(future.result())
            loaded_images.update(future.result())

        def resize_image(image, img_width, img_height):
            """
            将图片等比例缩放
            """
            # Get image's original width and height
            original_width, original_height = image.size

            # Calculate the new width and height based on the original aspect ratio and the maximum width and height
            aspect_ratio = original_width / original_height
            if aspect_ratio > 1:
                new_width = min(original_width, img_width)
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = min(original_height, img_height)
                new_width = int(new_height * aspect_ratio)

            # Resize the image and create an ImageTk object
            resized_image = image.resize((new_width, new_height))

            image_tk = ImageTk.PhotoImage(resized_image)

            return image_tk

        with ThreadPoolExecutor(6) as executor: # 创建线程池
            future_list = [executor.submit(load_image, index, path) for index,path in paths.items()] # 提交任务
        
        for future in as_completed(future_list):
            future.add_done_callback(get_result)
        
        for index,image in loaded_images.items():
           image=resize_image(image, img_width, img_height)
           loaded_images.update({index:image})
        
        return loaded_images


class Config(ttk.Frame):

    def __init__(self,root):
        super().__init__(root)
        global host_path,cookie,download_type,download_number
        #打开本地配置文件
        with open(config_path,'r',encoding='utf-8') as f:
            self.json_data = json.load(f)
            # 获取保存路径
            host_path = self.json_data.get('host_path')
            # 获取cookie
            cookie = self.json_data.get('cookie')
            # 下载的作品类型
            download_type = self.json_data.get('download_type')
            # 下载线程数
            download_number = download_number
            """
            download_type.update({'Getillusts':json_data.get('Getillusts')})
            download_type.update({'Getmanga':json_data.get('Getmanga')})
            download_type.update({'GetmangaSeries':json_data.get('GetmangaSeries')})
            download_type.update({'GetnovelSeries':json_data.get('GetnovelSeries')})
            download_type.update({'Getnovels':json_data.get('Getnovels')})
            """

        #获取保存路径
        self.set_download_path = ttk.StringVar()
        self.set_download_path.set(host_path)
        #self.set_download_path.set(self.download_path)
        self.set_download_path_label = ttk.Label(self,text="保存路径:",width=15)
        self.set_download_path_label.grid(row=0,column=0)
        self.set_download_path_entry = ttk.Entry(self,textvariable=self.set_download_path,width=35)
        self.set_download_path_entry.grid(row=0,column=1,columnspan=3)

        #获取浏览器Cookie
        #self.set_cookie.set(self.cookie)
        self.set_cookie_label = ttk.Label(self,text="浏览器Cookie:",width=15)
        self.set_cookie_label.grid(row=1,column=0)
        self.set_cookie_text = ttk.Text(self,width=35,height=10)
        self.set_cookie_text.insert(0.0, cookie)
        self.set_cookie_text.grid(row=1,column=1,columnspan=3)

        #复选框标签
        self.get_type_text = ttk.Label(master=self,text='目前只能下作者的',width=25,justify='left')
        self.get_type_text.grid(column=0,row=2,columnspan=2)
        self.download_type_text = ttk.Label(master=self,text='选择下载的作品类型',width=25,justify='left')
        self.download_type_text.grid(column=3,row=2,columnspan=2)
        #复选框内容
        self.get_type=[('标签(tag)',ttk.IntVar()),('作者(user)',ttk.IntVar())]
        self.download_type=[('插画(illusts)',ttk.IntVar()),('漫画(manga)',ttk.IntVar()),('漫画系列(mangaSeries)',ttk.IntVar()),
                            ('小说系列(novelSeries)',ttk.IntVar()),('小说(novels)',ttk.IntVar())]
        
        for a in range(5):
            type,status = download_type.popitem()
            if type == 'Getillusts':
                if status:self.download_type[0][1].set(1)
            elif type == 'Getmanga':
                if status:self.download_type[1][1].set(1)
            elif type == 'GetmangaSeries':
                if status:self.download_type[2][1].set(1)
            elif type == 'GetnovelSeries':
                if status:self.download_type[3][1].set(1)
            elif type == 'Getnovels':
                if status:self.download_type[4][1].set(1)
        self.get_checks = []
        self.download_checks = []
        self.setupUI()

    def setupUI(self):
        #创建复选框
        def choose_get_type():
            pass
            #for title,status in self.get_type:
                #if title == '作者(user)' and status.get() == 1:

                #if title == '标签(tag)' and status.get() == 1:

        def choose_download_type():
            for title,status in self.download_type:
                if title == '插画(illusts)' and status.get() == 1:download_type.update({'Getillusts':True})
                elif title == '插画(illusts)' and status.get() == 0:download_type.update({'Getillusts':False})
                if title == '漫画(manga)' and status.get() == 1:download_type.update({'Getmanga':True})
                elif title == '漫画(manga)' and status.get() == 0:download_type.update({'Getmanga':False})
                if title == '漫画系列(mangaSeries)' and status.get() == 1:download_type.update({'GetmangaSeries':True})
                elif title == '漫画系列(mangaSeries)' and status.get() == 0:download_type.update({'GetmangaSeries':False})
                if title == '小说系列(novelSeries)' and status.get() == 1:download_type.update({'GetnovelSeries':True})
                elif title == '小说系列(novelSeries)' and status.get() == 0:download_type.update({'GetnovelSeries':False})
                if title == '小说(novels)' and status.get() == 1:download_type.update({'Getnovels':True})
                elif title == '小说(novels)' and status.get() == 0:download_type.update({'Getnovels':False})
        
        def get_type_check():
            row = 3
            for title,status in self.get_type:
                get_check = ttk.Checkbutton(self,text=title,onvalue=1,offvalue=0,variable=status,width=25,
                                            command=choose_get_type)
                get_check.grid(column=0,row=row,padx=1,pady=1,columnspan=2)
                self.get_checks.append(get_check)
                #get_check.pack(anchor='w')
                row+=1
    
        def download_type_check():
            row = 3
            for title,status in self.download_type:
                download_check = ttk.Checkbutton(self,text=title,onvalue=1,offvalue=0,variable=status,width=25,
                                                command=choose_download_type)
                #get_check.pack(anchor='w')
                download_check.grid(column=2,row=row,padx=1,pady=1,columnspan=2)
                self.download_checks.append(download_check)
                row+=1
        
        get_type_check()
        download_type_check()
        choose_get_type()
        choose_download_type() 
        
        # 下拉列表框
        ttk.Label(self, text='下载线程数:', width=15).grid(column=0,row=8)
        self.download_number_box = ttk.Combobox(self, values= [1,2,3,4,5,6,7,8], state='readonly', width=10)
        self.download_number_box.current(download_number-1)
        self.download_number_box.bind('<<ComboboxSelected>>', self.select_download_number)
        self.download_number_box.grid(column=1,row=8)

        # 保存按钮
        self.save_button = ttk.Button(self,text='save',command=self.save_config,width=15)
        self.save_button.grid(column=0,row=9,padx=1,pady=1)
        
        # 手动备份按钮
        self.manual_backup_button = ttk.Button(self,text='backup',command=self.mongoDB_manual_backup,width=15)
        self.manual_backup_button.grid(column=1,row=9,padx=1,pady=1)
        # 停用
        self.manual_backup_button.config(default='disabled')

    def analyze_cookie(self,oringal_cookies):
        cookies = re.findall('.*?=.*?;',oringal_cookies,re.S)
        cookie = {}
        for oringal_cookie in cookies:
            key = re.search(".+?(?==)",oringal_cookie).group()
            value = re.search('(?<==).+(?=;)',oringal_cookie).group()
            cookie[key]=value
        return cookie

    def save_config(self):
        global cookie
        if re.search('first_visit_datetime_pc=',str(cookie)):
            cookie = self.analyze_cookie(cookie)
        self.set_cookie_text.delete(0.0, 'end')
        self.set_cookie_text.insert(0.0, cookie)
        with open(config_path,'w',encoding='utf-8') as f:
            self.json_data.update({"host_path":self.set_download_path.get(),"cookie":cookie,
                                    "download_type":download_type,"download_number":download_number})
            json.dump(self.json_data,f,ensure_ascii=False)
        a = Windows.update_config()
        del a

    def mongoDB_manual_backup(self):
        print("开始手动备份,请勿关闭程序!!!")
        now = 1
        all = len(db.list_collection_names())
        for name in db.list_collection_names():
            collection = db[name]
            a = collection.find({"id": { "$exists": True }},{ "_id": 0})
            for docs in a:
                if len(docs)==9:
                    b=backup_collection.find_one({"id":docs.get("id")})
                    if b:
                        if b.get('failcode'):
                            del b['failcode']
                        if b==docs:continue
                        else:c=backup_collection.find_one_and_update({"id":docs.get("id")},{"$set":docs})
                        if c:pass
                        else:
                            print('cao')
                            print(docs)
                    else:backup_collection.insert_one(docs)
            done = int(50 * now / all)
            sys.stdout.write("\r[%s%s] %d%%" % ('█' * done, ' ' * (50 - done), 100 * now / all))
            sys.stdout.flush()    
            now += 1
        print("手动备份完成")

    def select_download_number(self, event):
        global download_number
        download_number = int(self.download_number_box.get())

if __name__ == '__main__':
    Windows()