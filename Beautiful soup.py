from bs4 import BeautifulSoup
import requests
import re
import random
import urllib
from datetime import datetime
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from selenium import webdriver
import time
import jieba


USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]

class bilibili_video():
    def __init__(self,av):
        """
        :param av: a string which refers to the av number of videos in bilibili.
        """
        self.av_num=av
        self.headers = {'user-agent':random.choice(USER_AGENT_LIST)}
        self.url="https://www.bilibili.com/video/av"+av
        self.soup = BeautifulSoup(requests.get(self.url,headers=self.headers).text,features='lxml')


    def get_video_information(self):
        title = self.soup.find(name="span", attrs={"class": "tit"}).text
        author=self.soup.find(name="meta",attrs={"name":"author"})['content']

        information=(title,author)
        return information


    def get_clip_nums(self):
        clips_info=self.soup.find(name="script",string=re.compile("window.__INITIAL_STATE__")).text
        clips_info=re.findall(r'\"pages\"[^\]]+',clips_info)[0]
        clips=re.findall(r'\"cid\":[0-9]+',clips_info)
        clip_nums=[]
        for clip in clips:
            clip_num=clip.split(':')[-1]
            clip_nums.append(clip_num)

        return clip_nums


    def get_upload_time(self):
        upload_date=self.soup.find(name="meta",attrs={"itemprop":"uploadDate"})['content'][:10]
        time=datetime.strptime(upload_date,'%Y-%m-%d')

        return time.date()

    def get_video_image(self):
        # save the img to local directory
        image_url=self.soup.find(name="meta",attrs={"itemprop":"image"})['content']
        image_suffix=image_url.split('.')[-1]
        filename="bilibili/av"+self.av_num+"."+image_suffix
        urllib.urlretrieve(image_url,filename=filename)

    def get_popularity(self):
        para_url="http://api.bilibili.com/archive_stat/stat?aid="+self.av_num
        para_text=BeautifulSoup(requests.get(para_url).text,features='lxml')
        para_text=para_text.find(name="p")

        view=int(re.findall(r'\"view\":[^,]+',para_text)[0].split(':')[1])
        num_danmaku=int(re.findall(r'\"danmaku\":[^,]+',para_text)[0].split(':')[1])
        reply=int(re.findall(r'\"reply\":[^,]+',para_text)[0].split(':')[1])
        favorite=int(re.findall(r'\"favorite\":[^,]+',para_text)[0].split(':')[1])
        coin=int(re.findall(r'\"coin\":[^,]+',para_text)[0].split(':')[1])
        share=int(re.findall(r'\"share\":[^,]+',para_text)[0].split(':')[1])
        like=int(re.findall(r'\"like\":[^,]+',para_text)[0].split(':')[1])

        popularity=(view,num_danmaku,reply,favorite,coin,share,like)
        return popularity

    def get_tags(self):
        tags=self.soup.find_all(name="li",attrs={"class":"tag"})
        tag_list=[tag.text for tag in tags]

        return tag_list   # make sure to iterate the list to get the Chinese characters in Python 2.7


    def get_danmakus(self):
        danmaku_list_all_clips=[]
        for clip_num in self.get_clip_nums():
            danmaku_url="http://comment.bilibili.com/"+clip_num+".xml"
            danmaku_text=BeautifulSoup(requests.get(danmaku_url).content,features='lxml')
            danmakus=danmaku_text.find_all(name="d")
            danmaku_list=[danmaku.text for danmaku in danmakus]
            danmaku_list_all_clips.append(danmaku_list)

        return danmaku_list_all_clips


    def get_comment_example(self):
        # due to the duplicate comments in different pages, here we just fetch some examples
        comment_url="https://api.bilibili.com/x/v2/reply?jsonp=jsonp&type=1&oid="+self.av_num+"&sort=0"
        comment_text=BeautifulSoup(requests.get(comment_url).text,features='lxml')
        comment_text=comment_text.find(name="p").text
        comments=re.findall(r'\"message\":\"[^\"]+',comment_text)

        comments_example=[comment.split('\"')[3] for comment in comments if len(comment)>3]
        return comments_example[1:]   # the first comment is "0", so drop it


def get_search_av():
    headers = {'user-agent':random.choice(USER_AGENT_LIST)}
    # modify the following url if using Python 2.7 or change it as parameter for this function for Python 3
    url="https://search.bilibili.com/all?keyword=%E5%A4%8D%E6%97%A6"
    soup = BeautifulSoup(requests.get(url,headers=headers).text,features='lxml',from_encoding='utf-8')
    pages=soup.find_all(name="button",attrs={"class":"pagination-btn"})
    page_num=pages[-1].text
    print (page_num)


    av_nums = []
    for page in range(1,int(page_num)+1):
        print ("finished page {}/{}".format(page,page_num))
        url_with_page=url+"&page="+str(page)
        soup = BeautifulSoup(requests.get(url_with_page, headers=headers).text, features='lxml')
        videos=soup.find_all(name="li",attrs={"class":"video matrix"})
        for video in videos:
            time_length = video.find("span",attrs={"class":"so-imgTag_rb"}).text.split(':')
            # we just fetch videos with the whole length greater than 10 hours,
            # which are likely to be a course instead of a lecture
            if len(time_length)==3 and int(time_length[0])>10:
                av_num=video.find("span",attrs={"class":"type avid"}).text
                av_nums.append(av_num[2:])

    return av_nums


def save_to_dataframe(av_nums):
    """
    :param av_nums: a list of av_num.
    """
    video_data=pd.DataFrame(columns=['av_num','title','upload_time','author','view','num_danmaku',
                                     'reply','favorite','coin','share','like','tags'])
    for i,av_num in enumerate(av_nums):
        video=bilibili_video(av_num)
        title, author=video.get_video_information()
        upload_time=video.get_upload_time()
        view, num_danmaku, reply, favorite, coin, share, like=video.get_popularity()
        tags=video.get_tags()

        video_data.loc[i]=[av_num,title,upload_time,author,view,num_danmaku,reply,favorite,coin,share,like,tags]

    video_data.to_csv("bilibili/fudan.csv",encoding='utf-8')

class topic_analyser():
    def __init__(self,topic):
        """
        :param topic: string in ["physics","math","all"]
        """
        if topic=="physics":   # you can add more topics to analyse other given subjects
            self.video_data=pd.read_csv("bilibili/physics+fudan.csv")
            self.video_data.drop(columns=['Unnamed: 0'],inplace=True)
            self.video_data.drop(labels=[6,7,9,12,33,34],inplace=True)

    def plot_top_view(self):
        self.video_data.sort_values(by='view',ascending=False,inplace=True)
        top_10_view=self.video_data.head(10)
        label_list=top_10_view['av_num']
        view_list=top_10_view['view']
        rects = plt.bar(left=range(10), height=view_list, width=0.4, alpha=0.8, color='red',label="view")
        for rect in rects:
            height = rect.get_height()
            plt.text(rect.get_x() + rect.get_width() / 2, height+1, str(height), ha="center", va="bottom")
        plt.xticks(range(10),label_list,size=6)
        plt.legend()
        plt.show()

    def get_author(self):
        authors=self.video_data['author']
        print (authors.value_counts())   # "OriginLab" ranks highest as for the contribution in physics

    def view_between_danmaku(self):
        view=self.video_data['view']
        danmaku=self.video_data['num_danmaku']
        plt.scatter(x=view,y=danmaku,c='green')
        plt.xlabel("view")
        plt.ylabel("num_danmaku")
        plt.show()


    def plot_top_tags(self):
        all_tag=self.video_data['tags']
        tag_dict=defaultdict(int)
        for tags in all_tag:
            tags=tags[1:-1]
            tags=tags.split(',')
            for tag in tags:
                tag_dict[tag]+=1

        tag_dict=sorted(tag_dict.items(),key=lambda item:item[1],reverse=True)
        tag_list,tag_freq=zip(*tag_dict[:10])
        print (tag_list,tag_freq)
        rects=plt.bar(left=range(10), height=tag_freq, width=0.4, alpha=0.8, color='orange',label="tag_freq")
        for rect in rects:
            height = rect.get_height()
            plt.text(rect.get_x() + rect.get_width() / 2, height + 1, str(height), ha="center", va="bottom")
        plt.xticks(range(10), tag_list, size=6)
        plt.legend()
        plt.show()



def danmaku_analysis(av):
    video=bilibili_video(av)
    danmaku_list=[]
    danmakus=video.get_danmakus()
    for i,danmaku in enumerate(danmakus):
        print ("****************************")
        print (i)
        print ("****************************")
        for danmaku_per_clip in danmaku:
            danmaku_list.append(danmaku_per_clip)
            print (danmaku_per_clip)


class user_analyser():
    def __init__(self,url="https://space.bilibili.com/2173411/channel/detail?cid=14724"):
        """
        :param url: A specific channel page of some user.
        """
        self.driver=webdriver.Chrome("D:\MOOC\pycharm\PyCharm 2018.2\code\chromedriver.exe")
        self.driver.get(url)
        self.url=url
        self.videos_title=[]

    def scrap_page_videos(self):
        time.sleep(5)
        physics_source_page=self.driver.page_source
        soup=BeautifulSoup(physics_source_page,features='lxml')
        videos=soup.find_all("a",attrs={"class":"title"})
        for video in videos:
            self.videos_title.append(video.text)

    def get_title_dict(self):
        self.scrap_page_videos()
        while True:
            try:
                self.driver.find_element_by_class_name("be-pager-next").click()
                self.scrap_page_videos()
            except:
                break

        title_dict=defaultdict(int)
        for title in self.videos_title:
            print(title)
            words=jieba.cut(title)
            for word in words:
                if len(word)>1:
                    title_dict[word]+=1

        title_dict = sorted(title_dict.items(), key=lambda item: item[1], reverse=True)
        return title_dict


Originlab=user_analyser()
title_dict=Originlab.get_title_dict()
print(title_dict)