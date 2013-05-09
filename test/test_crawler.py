import os,sys,unittest,readline,re,datetime
sys.path.append(os.path.join(os.path.dirname(__file__),"../src/"))

from qur.crawler import Crawler
from dateutil import parser as datep

crawler = Crawler()

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

@crawler.save_handler
def save(objects):
    for obj in objects:
        data = obj["data"]
        print data["author"]

crawler.append_to_fetch_queue([
    'http://coolshell.cn/articles/3445.html',
    #'http://coolshell.cn',
    'http://www.ruanyifeng.com/blog/2013/05/boyer-moore_string_search_algorithm.html',
    ])

if __name__ == "__main__":
    crawler.spawn(1)

