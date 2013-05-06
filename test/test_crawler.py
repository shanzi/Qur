import os,sys,unittest,readline
sys.path.append(os.path.join(os.path.dirname(__file__),"../src/"))

from qur.crawler import Crawler

crawler = Crawler()

@crawler.handler_for("*","coolshell.cn")
def coolshell(proxy):
    if proxy.splited_url.path.startswith("/articles"):
        bst = proxy.bst
        if bst:
            post= bst.find('div',class_='post')
            title = bst.title.get_text()
            proxy.data['title'] = title
            proxy.data['post'] = post.get_text()
            post.decompose()
            proxy.data['side'] = bst.get_text()
    return True


@crawler.save_handler
def save(objects):
    for obj in objects:
        print obj["data"].get("post")

crawler.append_to_fetch_queue([
    'http://coolshell.cn',
    ])

crawler.spawn()

