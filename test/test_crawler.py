import os,sys,unittest,readline,re
sys.path.append(os.path.join(os.path.dirname(__file__),"../src/"))

from qur.crawler import Crawler
from dateutil import parser as datep

import pymongo
client = pymongo.MongoClient("dharma.mongohq.com",10011)
db = pymongo.database.Database(client,'fetch_data')
db.authenticate("","")


crawler = Crawler()

def parse_chinese_date(string):
    reg = re.compile(u'(\\d\\d\\d\\d)\u5e74(\\d{1,2})\u6708(\\d{1,2})\u65e5')
    sed = reg.search(string)
    if sed:
        return datep.parse('-'.join(sed.groups()[:3]))
    else:
        return ''



@crawler.handler_for("*","coolshell.cn")
def coolshell(proxy):
    if proxy.path.startswith("/articles"):
        post=proxy.find(".post")
        date=post.find(".info span.date")
        author = post.find(".info span.author")
        content = post.find(".content")
        title = post.find("h2")
        striped_date = re.compile(r"\D+").sub('-',date.text())
        tags = post.find("a[ref=tag]")

        proxy.data("author",author.text())
        proxy.data("title",title.text())
        proxy.data("date",datep.parse(striped_date))
        proxy.data("content",content.text())
        proxy.data("tags",[a.text() for a in tags.items()])

        content.remove()

        proxy.data("side",proxy.find("body").text())
    return True

@crawler.handler_for("*","ruanyifeng.com")
def ruanyifeng(proxy):
    if proxy.path.startswith("/blog"):
        if re.compile(r"/blog/\d{4}/\d{2}/.+").match(proxy.path):
            post = proxy.find(".hentry")
            title = post.find("#page-title")
            author = post.find(".author a").eq(0)
            date = post.find(".published[title]").attr("title")
            content = post.find("#main-content")

            proxy.data("author",author.text())
            proxy.data("title",title.text())
            proxy.data("date",datep.parse(date))
            proxy.data("content",content.text())

            content.remove()

            proxy.data("side",post.text())
        return True

@crawler.handler_for("*","linuxtoy.org")
def linuxtoy(proxy):
    if proxy.path.startswith("/archives"):
        if re.compile(r"^/archives/\d\d\d\d/\d\d/?").match(proxy.path):
            return True
        elif proxy.path == "/archives": return True

        post = proxy.find(".post")
        title = post.find("h2").text()
        tagsauchors = post.find(".postmeta a[rel=tag]")
        author = post.find("a[rel=author]").text()
        datestr = post.find(".postmeta").text()
        content=post.find(".entry")
        content.find(".entrylist").remove()

        datematch=re.compile(r"\d{4}-\d\d-\d\d").search(datestr)
        tags = [ a.text() for a in tagsauchors.items()]

        if datematch:
            proxy.data("date",datep.parse(datematch.group()))

        proxy.data("title",title)
        proxy.data("author",author)
        proxy.data("content",content.text())
        proxy.data("tags",tags)

        content.remove()

        proxy.data("side",proxy.body.text())

        return True
    elif proxy.path.startswith("/category"):
        return True
    elif proxy.path == "":
        return True
    else: return False

@crawler.handler_for("www","oschina.net")
def oschina(proxy):
    if re.compile(r"^/news/\d+/.+").match(proxy.path):
        cate = proxy.find("a[href='/news/list?show=project']")
        if len(cate)<1:
            return False

        post = proxy.find(".NewsEntity")
        post.find(".NewsToolbar").remove()

        content = post.find(".NewsContent").text()
        author = post.find(".PubDate a").eq(0).text()
        title = post.find("h1.OSCTitle").text()
        date = parse_chinese_date(post.find(".PubDate").text())
        
        post.find(".NewsContent").remove()
        
        proxy.data("title",title)
        proxy.data("author",author)
        proxy.data("date",date)
        proxy.data("content",content)
        proxy.data("side",proxy.body.text())

        return True
    elif proxy.path.startswith("/news/list") and \
            "project" in proxy.query.get("show"):
        proxy.find(".HotNewsList").remove()
        return True
    else:
        return False





@crawler.save_handler
def save(objects):
    db.test_fetch.insert(objects)
    #for obj in objects:
    #    if obj.get("data"):
    #        print obj["data"].get("author")

crawler.append_to_fetch_queue([
    #'http://coolshell.cn',
    #'http://www.ruanyifeng.com/blog/',
    'http://linuxtoy.org/',
    'http://www.oschina.net/news/list?show=project',
    ])

if __name__ == "__main__":
    crawler.spawn(1)

