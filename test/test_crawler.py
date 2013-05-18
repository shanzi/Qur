import os,sys,unittest,readline,re
sys.path.append(os.path.join(os.path.dirname(__file__),"../src/"))

from qur.crawler import Crawler
from qur import GenericIndexer
from dateutil import parser as datep
import jieba

import pymongo

DEBUG = True

if not DEBUG:
    client = pymongo.MongoClient("dharma.mongohq.com",10011)
    db = pymongo.database.Database(client,'fetch_data')
    db.authenticate("","")

crawler = Crawler(DEBUG)

def parse_chinese_date(string):
    reg = re.compile(u'(\\d\\d\\d\\d)\u5e74(\\d{1,2})\u6708(\\d{1,2})\u65e5')
    sed = reg.search(string)
    if sed:
        return datep.parse('-'.join(sed.groups()[:3]))
    else:
        return ''



@crawler.handler_for("*","coolshell.cn")
def coolshell(proxy):
    if re.compile(r"^/articles/\d+\.html").match(proxy.path):
        post=proxy.find(".post")
        date=post.find(".info span.date")
        author = post.find(".info span.author")
        content = post.find(".content")
        title = post.find("h2")
        striped_date = re.compile(r"\D+").sub('-',date.text())
        tags = post.find("a[rel=tag]")

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
    elif proxy.path == "" or proxy.path == "/":
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

@crawler.handler_for("www","wired.com")
def wired(proxy):
    if re.compile(r"^/(reviews|gadgetlab)/\d{4}/\d{2}/.+").match(proxy.path):
        post = proxy.find(".post")
        title = post.find("h1").text()+ '-' + post.find("h2").text()
        datetime_s = post.find(".entryDate").eq(0).text() + ' ' \
                + post.find(".entryTime").eq(0).text()
        tags = post.find(".entryCategories a").text()
        if tags: tags = [s.strip() for s in tags.split("&")]
        else: tags = []
        author = proxy.find("meta[name=Author]").attr("content")
        datetime = datep.parse(datetime_s.replace('|',' '),fuzzy=True)
        category = proxy.find("meta[name=Subsection]").attr("content").lower()
        content = post.find(".entry").text()
        post.remove()
        side = proxy.body.text()

        proxy.data("title",title)
        proxy.data("tags",tags)
        proxy.data("author",author)
        proxy.data("category",category)
        proxy.data("date",datetime)
        proxy.data("content",content)
        proxy.data("side",side)
        
        return True
    elif proxy.path.startswith("/reviews") or proxy.path.startswith("/gadgetlab"):
        return True
    else:
        return False


@crawler.handler_for("www","36kr.com")
def kr(proxy):
    if proxy.path.startswith("/p/"):
        proxy.log(type(proxy.content))
        post = proxy.find(".entry-content")
        title = post.find("h1.entry-title").text()
        tags = [a.text() for a in post.find("a.tag").items()]
        content = post.find(".mainContent").text()
        category = proxy.find("ul.breadcrumb li a").eq(1).text()
        author = post.find(".uname").eq(0).text()
        date = datep.parse(post.find("abbr.timeago").attr("title"))
        post.remove()
        side = proxy.body.text()

        proxy.data("title",title)
        proxy.data("content",content)
        proxy.data("category",category)
        proxy.data("author",author)
        proxy.data("date",date)
        proxy.data("side",side)
        proxy.data("tags",tags)

    return True

@crawler.handler_for("www","appinn.com")
def appinn(proxy):
    if proxy.path=="/" or proxy.path =="" \
            or proxy.path.startswith("/category"):
        return True
    else:
        post = proxy.find(".post")
        title = post.find(".entry-title").text()
        author = post.find(".entry-meta a[rel=author]").eq(0).text()
        date = datep.parse(post.find(".entry-meta cite").text())
        tags = [a.text() for a in post.find(".entry-meta a[rel=tag]").items()]
        target = [a.attr("href") for a in post.find("img.imgdown").nextAll("a[href]").items()]
        content = post.find(".entry-content").text()
        post.find(".entry-content").remove()
        side = proxy.body.text()

        proxy.data("title",title)
        proxy.data("author",author)
        proxy.data("date",date)
        proxy.data("tags",tags)
        proxy.data("target",target)
        proxy.data("content",content)
        proxy.data("side",side)

        return True

@crawler.handler_for("*","techcrunch.com")
def techcrunch(proxy):
    if re.compile(r"/?\d{4}/\d{2}/.+").match(proxy.path):
        post = proxy.find("#module-post-detail")
        title = post.find("h1.headline").text()
        author = post.find(".author span.name").text()
        category = proxy.find(".post-category-name").text()
        tags = [a.text() for a in proxy.find("a[rel=tag]").items()]
        content = post.find(".body-copy").text()
        post.remove()
        side = proxy.body.text()

        proxy.data("title",title)
        proxy.data("author",author)
        proxy.data("tags",tags)
        proxy.data("category",category)
        proxy.data("content",content)
        proxy.data("side",side)
    return True


@crawler.handler_for("*","solidot.org")
def solidot(proxy):
    if proxy.path.startswith("/story"):
        title = proxy.find(".bg_htit h2").text()
        content = proxy.find(".p_mainnew").text()
        date = parse_chinese_date(proxy.find(".talk_time").text())

        proxy.find(".block_m").remove()

        side = proxy.body.text()

        proxy.data("title",title)
        proxy.data("content",content)
        proxy.data("date",date)
        proxy.data("side",side)
    elif proxy.path.startswith("/comments"):
        return False
    elif proxy.path.startswith("/~"):
        return False

    return True

@crawler.handler_for("*","slashdot.org")
def slashdot(proxy):
    if re.compile("^/story/\d{2}/\d{2}/\d{2}/\d+/.+").match(proxy.path):
        title = proxy.find("h2.story span").text()
        content = proxy.find(".body .p i").text()

        proxy.find(".body .p i").remove()
        author = proxy.find(".body .p").text().replace("writes","")
        date = datep.parse(proxy.find("time").text(),fuzzy=True)
        proxy.find("articles").remove()
        side = proxy.body.text()
        category = proxy.netloc.split(".")[0]

        proxy.data("title",title)
        proxy.data("author",author)
        proxy.data("category",category)
        proxy.data("date",date)
        proxy.data("content",content)
        proxy.data("side",side)
    elif proxy.path.startswith("/comments"):
        return False
    elif proxy.path.startswith("/video"):
        return False
    elif proxy.path.startswith("/~"):
        return False

    return True








@crawler.save_handler
def save(objects):
    db.test_fetch.insert(objects)

@crawler.debug_save_handler
def debug_dave(objects):
    for obj in objects:
        if obj.get("data"):
            print obj.get('data').get("title")
            print obj.get('data').get("author")
            print obj.get('data').get("date")
            print obj.get('data').get("category")
            print obj.get('data').get("tags")

crawler.append_to_fetch_queue([
    #'http://coolshell.cn',
    #'http://www.ruanyifeng.com/blog/',
    #'http://linuxtoy.org/',
    #'http://www.oschina.net/news/list?show=project',
    #'http://www.wired.com/reviews/',
    #'http://www.36kr.com/p/203192.html',
    #'http://www.appinn.com/',
    #'http://techcrunch.com/',
    #'http://www.solidot.org/',
    #'http://www.slashdot.org/',
    ])

def index():
    gi = GenericIndexer(db,"test",jieba)
    datas = db.test_fetch.find()
    total = db.test_fetch.count()
    indexed = 0
    for data in datas:
        gi.indexText(data["_id"],data["data"]["content"])
        indexed+=1
        print "indexed %d/%d (%f %)" % indexed,total,(float(indexed)/total *10)

    print "finished" 


if __name__ == "__main__":
    #crawler.spawn(1)


