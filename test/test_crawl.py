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

DEBUG = True
if not DEBUG:
    import pymongo
    from pymongo import MongoClient
    client = MongoClient("dharma.mongohq.com")
    db = pymongo.database.Database(client,"database")
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


@crawler.handler_for("www","pcworld.com")
@crawler.handler_for("www","macworld.com")
@crawler.handler_for("www","techhive.com")
def techhive(proxy):
    if re.compile(r"/article/\d+/.+\.html").match(proxy.path):
        proxy.data("title",proxy.find("h1").text())
        proxy.data("author",proxy.find("a[itemprop=author]").text())
        proxy.data("datetime",datep.parse(proxy.find("li[itemprop=datePublished]").text()))
        proxy.data("tags",[a.text() for a in proxy.find(".tags").items()])
        proxy.data("content",proxy.find("section.page").text())
        if proxy.find("div.review-navbar"):
            proxy.data("category","review")
        else:
            proxy.data("category",proxy.find("a.topCatLink").text())

    if proxy.netloc in ["www.techhive.com","www.macworld.com","www.pcworld.com"]:
        return True
    else: False


@crawler.handler_for("www","maclife.com")
def maclife(proxy):
    match= re.compile(r"/article/(\w+)/.+").match(proxy.path)
    if match:
        proxy.data("title",proxy.find("h1.title_smaller").text())
        proxy.data("author", proxy.find("span.posted_by").text()[4:])
        proxy.data("datetime",
                    datep.parse(
                        proxy.find("span.posted_date").text()[7:],
                        fuzzy=True
                        )
                    )
        proxy.data("tags",
                   [a.text() for a in proxy.find("a[rel=tag]").items()])
        proxy.data("category",match.groups()[0])
        proxy.data("content",proxy.find("div.node_article p").text())
    return True


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
            print "len of content: %d" % len(data.get("content"))

FETCH_URLS=[
        "http://news.cnet.com",
        "http://reviews.cnet.com",
        "http://www.macworld.com/",
        "http://www.pcworld.com/",
        "http://www.techhive.com/",
        "http://www.maclife.com/"
        ]

    

def main():
    crawler.append_to_fetch_queue(FETCH_URLS)
    if DEBUG:
        crawler.spawn(1)
    else:
        crawler.spawn(len(FETCH_URLS))

if __name__=="__main__":
    main()

