#! /usr/bin/env python
# encoding:utf8
# vim: set ts=4 et sw=4 sts=4

"""
File: test_crawl.py
Author: shanzi
Email: shanzi@diumoo.net
Url: U{http://github.com/shanzi/Qur}
Description: crawling web for data dig
"""

import os
import sys
import re
sys.path.append(os.path.join(os.path.dirname(__file__),"../src/"))

from qur.crawler import Crawler
from dateutil import parser as datep

DEBUG = False
if not DEBUG:
    import pymongo
    from pymongo import MongoClient
    client = MongoClient("dharma.mongohq.com",10012)
    db = pymongo.database.Database(client,"fetch_data")
    db.authenticate("","")
    

crawler = Crawler(DEBUG)

@crawler.handler_for("news","cnet.com")
def news_cnet(proxy):
    if re.compile(r"^/[0-9\-_]+/\w+").match(proxy.path):
        post = proxy.find("div.post")
        proxy.data("title"             , post.find("h1").text())
        proxy.data("author"            , post.find("a[rel=author]").text())
        proxy.data("datetime"          , datep.parse(post.find("time.datestamp").text()))
        proxy.data("content"           , post.find("div.postBody").text())
        proxy.data("category"          , "news")
        proxy.data("tags"              , [a.text() for a in post.find("div.postLinks a").items()])
    if proxy.netloc != "news.cnet.com" : return False
    else: return True

@crawler.handler_for("reviews","cnet.com")
def review_cnet(proxy):
    matches=re.compile(r"^/([\w-]+)(/[\w-]+/[0-9\-_]+\.html)?").match(proxy.path)
    if matches:
        sum = proxy.find("div#reviewSummary")
        cnetr = proxy.find("article#cnetReview")
        if sum or cnetr:
            content =""
            if sum: content+=sum.text()
            if cnetr: content += cnetr.text()
            proxy.data("title"    , proxy.find("h1").text())
            proxy.data("content"  , content)
            proxy.data("category" , "review")
            proxy.data("tags"     , [matches.groups()[0],])
    if proxy.netloc != "reviews.cnet.com" : return False
    else: return True

@crawler.save_handler
def save(tosave):
    db.test_fetch.insert(tosave)

@crawler.debug_save_handler
def debug_save(objects):
    for obj in objects:
        data = obj.get("data")
        if data:
            print data.get("title")
            print data.get("author")
            print data.get("datetime")
            print data.get("category")
            print data.get("tags")

FETCH_URLS=[
        "http://reviews.cnet.com/tablets/hisense-sero-7-lt/4505-3126_7-35771057.html",
        #"http://news.cnet.com",
        #"http://reviews.cnet.com"
        ]

    

def main():
    crawler.append_to_fetch_queue(FETCH_URLS)
    crawler.spawn(2)

if __name__=="__main__":
    main()

