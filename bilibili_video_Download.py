import requests, time, hashlib, urllib.request, re, json
from moviepy.editor import *
import os, sys, threading
import imageio
import pymongo
import pandas as pd
import socket
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()
imageio.plugins.ffmpeg.download()

"""
下载指定作者的所有视频
"""

# 下载视频
'''
 urllib.urlretrieve 的回调函数：
def callbackfunc(blocknum, blocksize, totalsize):
    @blocknum:  已经下载的数据块
    @blocksize: 数据块的大小
    @totalsize: 远程文件的大小
'''


def Schedule_cmd(blocknum, blocksize, totalsize):
    speed = (blocknum * blocksize) / (time.time() - start_time)
    # speed_str = " Speed: %.2f" % speed
    speed_str = " Speed: %s" % format_size(speed)
    recv_size = blocknum * blocksize

    # 设置下载进度条
    f = sys.stdout
    pervent = recv_size / totalsize
    percent_str = "%.2f%%" % (pervent * 100)
    n = round(pervent * 50)
    s = ('#' * n).ljust(50, '-')
    p = f.write(percent_str.ljust(8, ' ') + '[' + s + ']' + speed_str)
    print(p)
    f.flush()
    f.write('\r')



# 字节bytes转化K\M\G
def format_size(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
        return "Error"
    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
            G = M / 1024
            return "%.3fG" % (G)
        else:
            return "%.3fM" % (M)
    else:
        return "%.3fK" % (kb)



# 访问API地址
def get_play_list(start_url, cid, quality):
    entropy = 'rbMCKn@KuamXWlPMoJGsKcbiJKUfkPF_8dABscJntvqhRSETg'
    appkey, sec = ''.join([chr(ord(i) + 2) for i in entropy[::-1]]).split(':')
    params = 'appkey=%s&cid=%s&otype=json&qn=%s&quality=%s&type=' % (appkey, cid, quality, quality)
    chksum = hashlib.md5(bytes(params + sec, 'utf8')).hexdigest()
    url_api = 'https://interface.bilibili.com/v2/playurl?%s&sign=%s' % (params, chksum)
    headers = {
        'Referer': start_url,  # 注意加上referer
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    # print(url_api)
    html = requests.get(url_api, headers=headers).json()
    # print(json.dumps(html))
    video_list = []
    for i in html['durl']:
        video_list.append(i['url'])
    # print(video_list)
    return video_list

#  下载视频
def down_video(video_list, title, start_url, page,author_name):
    socket.setdefaulttimeout(60)
    num = 1
    print('[正在下载P{}段视频,请稍等...]:'.format(page) + title)
    currentVideoPath = os.path.join(sys.path[0], 'bilibili_video', author_name,title)  # 当前目录作为下载目录
    if not os.path.exists(currentVideoPath):
        os.makedirs(currentVideoPath)
    for i in video_list:
        opener = urllib.request.build_opener()
        # 请求头
        opener.addheaders = [
            # ('Host', 'upos-hz-mirrorks3.acgvideo.com'),  #注意修改host,不用也行
            ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
            ('Accept', '*/*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate, br'),
            ('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
            ('Referer', start_url),  # 注意修改referer,必须要加的!
            ('Origin', 'https://www.bilibili.com'),
            ('Connection', 'keep-alive'),
        ]
        urllib.request.install_opener(opener)
        # 开始下载
        if len(video_list) > 1:
            if not os.path.exists(os.path.join(currentVideoPath, r'{}-{}.flv'.format(title, num))):
                try:
                    urllib.request.urlretrieve(url=i,
                                               filename=os.path.join(currentVideoPath, r'{}-{}.flv'.format(title, num)),
                                               reporthook=Schedule_cmd)  # 写成mp4也行  title + '-' + num + '.flv'
                except socket.timeout:
                    count = 1
                    while count <= 3:
                        try:
                            urllib.request.urlretrieve(url=i, filename=os.path.join(currentVideoPath,
                                                                                    r'{}-{}.flv'.format(title, num)),
                                                       reporthook=Schedule_cmd)  # 写成mp4也行  title + '-' + num + '.flv'
                            break
                        except socket.timeout:
                            err_info = 'Reloading for %d time' % count if count == 1 else 'Reloading for %d times' % count
                            print(err_info)
                        count += 1

                    if count > 3:
                        print("downloading picture fialed!")
        else:
            if not os.path.exists(os.path.join(currentVideoPath, r'{}.flv'.format(title))):
                try:
                    urllib.request.urlretrieve(url=i, filename=os.path.join(currentVideoPath, r'{}.flv'.format(title)),
                                               reporthook=Schedule_cmd)  # 写成mp4也行  title + '-' + num + '.flv'
                except socket.timeout:
                    count = 1
                    while count <= 5:
                        try:
                            urllib.request.urlretrieve(url=i,
                                                       filename=os.path.join(currentVideoPath, r'{}.flv'.format(title)),
                                                       reporthook=Schedule_cmd)  # 写成mp4也行  title + '-' + num + '.flv'
                            break
                        except socket.timeout:
                            err_info = 'Reloading for %d time' % count if count == 1 else 'Reloading for %d times' % count
                            print(err_info)
                        count += 1
                    if count > 3:
                        print("downloading picture fialed!")
        num += 1



# 合并视频
def combine_video(title_list,author_name):
    video_path = os.path.join(sys.path[0], 'bilibili_video')  # 下载目录
    for title in title_list:
        current_video_path = os.path.join(video_path,author_name,title)
        if len(os.listdir(current_video_path)) >= 2:
            # 视频大于一段才要合并
            print('[下载完成,正在合并视频...]:' + title)
            # 定义一个数组
            L = []
            # 遍历所有文件
            for file in sorted(os.listdir(current_video_path), key=lambda x: int(x[x.rindex("-") + 1:x.rindex(".")])):
                # 如果后缀名为 .mp4/.flv
                if os.path.splitext(file)[1] == '.flv':
                    # 拼接成完整路径
                    filePath = os.path.join(current_video_path, file)
                    # 载入视频
                    video = VideoFileClip(filePath)
                    # 添加到数组
                    L.append(video)
            # 拼接视频
            final_clip = concatenate_videoclips(L)
            # 生成目标视频文件
            final_clip.to_videofile(os.path.join(current_video_path, r'{}.mp4'.format(title)), fps=24,
                                    remove_temp=False)
            print('[视频合并完成]' + title)
        else:
            # 视频只有一段则直接打印下载完成
            print('[视频合并完成]:' + title)


def get_aid(author_name):
    #从数据库中获取某个作者所有视频的aid，以列表的形式返回
    client = pymongo.MongoClient('localhost', 27017)
    db = client['test']
    table = db['bilibili_id']
    if table.find({'author_name': author_name}):
        table = table.find({'author_name': author_name})
        aid_list = []
        #table[:30]表示取30个视频，若想取所有，则改成table
        for one in table[:30]:
            aid_list.append(str(one['aid']))
        return aid_list
    else:
        print('输入错误')



if __name__ == '__main__':
    #默认下载480p清晰度视频,可以修改quality数值切换清晰度
    # 输入作者的名字,从数据库中获取作者所有视频的aid 如:木鱼水心  注意：get_aid默认只取30个，可以自行更改设置
    #或者输入作者某个视频的aid或者视频链接，单独下载某个视频也可 如:752607403  或 https://www.bilibili.com/video/av752607403
    author_name = input('请输入视频作者:')
    if author_name.isdigit() == True or 'https://www.bilibili.com/video/av' in author_name :
        aid_list = []
        aid_list.append(author_name)
    else:
        aid_list =get_aid(author_name)

    for start in aid_list:
        if start.isdigit() == True:  # 如果输入的是av号
            # 获取cid的api, 传入aid即可
            start_url = 'https://api.bilibili.com/x/web-interface/view?aid=' + start
        else:
            # https://www.bilibili.com/video/av46958874/?spm_id_from=333.334.b_63686965665f7265636f6d6d656e64.16
            start_url = 'https://api.bilibili.com/x/web-interface/view?aid=' + re.search(r'/av(\d+)/*', start).group(1)

        # 视频质量
        # <accept_format><![CDATA[flv,flv720,flv480,flv360]]></accept_format>
        # <accept_description><![CDATA[高清 1080P,高清 720P,清晰 480P,流畅 360P]]></accept_description>
        # <accept_quality><![CDATA[80,64,32,16]]></accept_quality>
        # input('请输入您要下载视频的清晰度(1080p:80;720p:64;480p:32;360p:16)(填写80或64或32或16):')
        quality = '32'
        # 获取视频的cid,title
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
        }
        html = requests.get(start_url, headers=headers).json()
        data = html['data']
        cid_list = []
        if '?p=' in start:
            # 单独下载分P视频中的一集
            p = re.search(r'\?p=(\d+)', start).group(1)
            cid_list.append(data['pages'][int(p) - 1])
        else:
            # 如果p不存在就是全集下载
            cid_list = data['pages']
        # print(cid_list)
        # 创建线程池
        threadpool = []
        title_list = []
        num = 1
        p = '-'
        if len(cid_list) >1:
            num = 1
            p = '-'
        else:
            num = ''
            p = ''
        for item in cid_list:
            cid = str(item['cid'])
            #由于某个视频有多个分p,故加上num
            title = data['title']+p+str(num)
            title = re.sub(r'[\/\\:*?"<>|]', '', title) # 替换为空的
            print('[下载视频的aid]:' + start)
            print('[下载视频的cid]:' + cid)
            print('[下载视频的标题]:' + title)
            title_list.append(title)
            page = str(item['page'])
            start_url = start_url + "/?p=" + page
            video_list = get_play_list(start_url, cid, quality)
            start_time = time.time()
            # down_video(video_list, title, start_url, page,author_name)
            # 定义线程
            th = threading.Thread(target=down_video, args=(video_list, title, start_url, page,author_name))
            # 将线程加入线程池
            threadpool.append(th)
            if num:
                num += 1

        # 开始线程
        for th in threadpool:
            th.start()
        # 等待所有线程运行完毕
        for th in threadpool:
            th.join()

        # 最后合并视频
        print(title_list)
        combine_video(title_list,author_name)
    print('下载完成')

