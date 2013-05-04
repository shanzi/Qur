##
# @file __init__.py
# @brief a simple web crawler
# @author U{Chase.Zhang<mailto:chase.zhang@diumoo.net}
# @date 2013-04-26


from bs4 import BeautifulSoup
from urlparse import urlsplit,urljoin,urlunsplit
import requests,logging

__MAX_FETCHED_URLS_CAPACITY__=10000
__MAX_FETCH_QUEUE_CAPACITY__=100000

logging.basicConfig(level=logging.DEBUG)
logger = logging

class ContentProxy(object):
    def __init__(self, url):
        super(ContentProxy, self).__init__()
        o = urlsplit(url)
        self.url=urlunsplit((o.scheme,o.netloc,o.path,o.query,'')).strip(" /#")
        self.splited_url=o
        self.redirect_count = 0
        self.data={}
        self._content=None
        self._bst=None
        self._links=None

    def fetch(self,url):
        logger.info("fetching url: " + url)
        try:
            res=requests.get(url,timeout=10)
        except Exception, e:
            logger.error("fetch error: %s",str(e))
            return False
        else:
            if res.status_code == 200:
                logger.info(
                        "fetched url:" + url + \
                        ", redirect count: " + str(len(res.history)) + \
                        ", response length:" + str(len(res.text)))
                self._content=res.text
                self.redirect_count=len(res.history)

    def __content__(self):
        if not self._content:
            self.fetch(self.url)
        return self._content

    def __bstree__(self):
        if not self._bst:
            self._bst = BeautifulSoup(self.content,"lxml")
        return self._bst

    def __links__(self):
        if self._links==None:
            lk=[]
            urls = [a["href"] for a in self.bst.find_all("a") \
                        if a["href"] and not a["href"].startswith("#")]
            for url in urls:
                joined = urljoin(self.url,url)
                if joined.startswith(("http","https")):
                    lk.append(joined)
            self._links=lk
        return self._links


    def __iter__(self):
        def iterator():
            yield ("url",self.url)
            yield ("links",self.links)
            yield ("redirect_count",self.redirect_count)
            yield ("data",self.data)
        return iterator()

    def __getattr__(self,k):
        if k== "content":
            return self.__content__()
        elif k == "links":
            return self.__links__()
        elif k == "bst":
            return self.__bstree__()
        else:
            super(ContentProxy,self).__getattr__(k)


class Crawler(object):
    def __init__(self):
        super(Crawler, self).__init__()
        self.fetched_urls = set()
        self.fetch_queue = []
        self.save_queue = []
        self.handlers = {}
        self._default_handler = None
        self._save_handler = None

    def get_handler_for(self,netloc):
        components=netloc.split(".")
        if len(components) <2: return None
        for i in range(len(components)-1):
            subdomain = '.'.join(components[:i])
            domain = '.'.join(components[i:])
            dhandler = self.handlers.get(domain)
            if dhandler:
                subh = dhandler.get(subdomain)
                if subh: return subh
                elif dhandler.get('*'):
                    return dhandler.get('*')
        return self._default_handler

    def handler_for(self,subdomain,domain,force_https=False):
        def wraped(handler):
            d = self.handlers.get(domain)
            if not d: self.handlers[domain]={}
            self.handlers[domain][(subdomain or '')] = handler
            return handler
        return wraped

    def default_handler(self,fn):
        self._default_handler = fn

    def process(self,url):
        proxy = ContentProxy(url)
        if proxy.url in self.fetched_urls:
            return

        handler = self.get_handler_for(proxy.splited_url.netloc)
        if handler and handler(proxy):
            logger.info("processing url: "+url)
            self.append_to_fetch_queue(proxy.links)
            self.append_to_save_queue(proxy)
            self.append_to_fetched_urls([proxy.url,])
        else:
            logger.warn("no handler for url : " + proxy.url)

    def append_to_fetch_queue(self,urls):
        if len(self.fetch_queue)<__MAX_FETCHED_URLS_CAPACITY__:
            self.fetch_queue.extend(urls)

    def append_to_save_queue(self,proxy):
        self.save_queue.append(dict(proxy))
        if len(self.save_queue) > 200:
            self.save()

    def append_to_fetched_urls(self,urls):
        if len(self.fetched_urls)> __MAX_FETCH_QUEUE_CAPACITY__:
            self.fetched_urls.clear()
        self.fetched_urls.update(urls)

    def save_handler(self,fn):
        self._save_handler = fn
        return fn

    def save(self):
        logger.info("saving: save queue length: " + str(len(self.save_queue)))
        if self._save_handler and self.save_queue:
            self._save_handler(self.save_queue)
            self.save_queue=[]

    def crawl(self):
        url = self.fetch_queue.pop()
        self.process(url)
