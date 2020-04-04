# bilibili-spider
利用pyspider爬取b站作者视频的所有aid，再批量下载作者的所有视频


1、在pyspider新建一个项目，将bilibili_aid中的代码复制到项目中

2、打开b站，进入你要爬取的作者的主页，切换到“投稿”选项，将形如https://space.bilibili.com/XXXXXX/video的链接复制到pyspider项目中的
def index_page(self, response):函数下 （前面的on_start函数不起作用，不用理会）

3、进行爬取，爬取结果会存储在mongodb下（需要对pyspider进行config配置，默认配置是不会存储在mongodb中的）

4、打开bilibili_video_download.py，输入上一步作者的名称，就可以进行视频批量下载 bilibili_video_download.py该文件也可单独使用，
直接输入视频链接如https://www.bilibili.com/video/av1002840xx 或者10028XX43 也可单独下载某个视频
