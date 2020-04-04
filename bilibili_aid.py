from pyspider.libs.base_handler import *
from urllib.parse import urlencode
import re
import requests
import json
import pymongo
import time
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Handler(BaseHandler):
    crawl_config = {
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.116 Safari/537.36',
    }
    # 在此处输入搜索关键词和爬取的页数
    keyword = '动漫'
    page = 1
    client = pymongo.MongoClient(host='127.0.0.1', port=27017)
    db = client['test']

    @every(minutes=24 * 60)
    def on_start(self):
        base_url = 'https://search.bilibili.com/all?'
        data = {}
        data['keyword'] = self.keyword
        for i in range(1, self.page + 1):
            data['page'] = str(i)
            url = base_url + urlencode(data)
            self.crawl(url, callback=self.index_page, headers=self.headers, validate_cert=False)

    # 进入作者的主页
    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        #进入作者的主页，切换到投稿选项，复制链接到下方author_url
        author_url = 'https://space.bilibili.com/50329118/video'
        self.crawl(author_url, callback=self.detail_page, headers=self.headers, validate_cert=False, fetch_type='js')

    # 获取作者信息
    @config(priority=2)
    def detail_page(self, response):
        total_video = response.doc('.cur > .num').text()
        author_name = response.doc('#h-name').text()
        # 开始遍历每一个视频的信息
        author_id = re.search(r'com/(\d+)/video', response.url).group(1)
        video_params = {
            'mid': author_id,
            'ps': '30',
            'jsonp': 'jsonp',
        }
        pages = int(total_video) // 30 + 2
        for page in range(1, pages):
            video_params['pn'] = str(page)
            video_message_url = 'https://api.bilibili.com/x/space/arc/search?' + urlencode(video_params)
            r = requests.get(video_message_url, headers=self.headers, verify=False)
            datas = json.loads(r.text).get('data').get('list').get('vlist')
            for data in datas:
                id = {
                    'bvid': data.get('bvid'),
                    'aid': data.get('aid'),
                    'author_name': author_name,
                    'video_name': data.get('title'),
                }
                self.db['bilibili_id'].insert(id)

    def on_result(self, result):
        if not result:
            return