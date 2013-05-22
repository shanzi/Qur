##
# @file __init__.py
# @brief a simple web crawler
# @author U{Chase.Zhang<mailto:chase.zhang@diumoo.net}
# @date 2013-04-26


from gevent import monkey; monkey.patch_all()
import gevent

import logging,time,random,signal,sys
import requests

from urlparse import urlsplit,urljoin,urlunsplit,parse_qs
from collections import deque

from pyquery import PyQuery


__MAX_FETCHED_URLS_CAPACITY__=100000
__MAX_FETCH_QUEUE_CAPACITY__=10000

logging.basicConfig(level=logging.INFO)
logger = logging



class ContentProxy(object):
    def __init__(self, url):
        super(ContentProxy, self).__init__()
        o = urlsplit(url)
        self.url=urlunsplit((o.scheme,o.netloc,o.path,o.query,'')).strip(" /#")
        self.splited_url=o
        self.redirect_count = 0
        self._data={}
        self._content=None
        self._document=None
        self._links=None
        self.encoding = "utf-8"
        self._request_headers = {
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Connection':'keep-alive',
                'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.43 Safari/537.31',
                }

    def fetch(self,url):
        logger.info("fetching url: " + url)
        try:
            res=requests.get(url,timeout=10,headers=self._request_headers)
        except Exception, e:
            logger.error("fetch error: %s",str(e))
            return False
        else:
            if res.status_code == 200:
                logger.info(
                        "fetched url:" + url + \
                        ", redirect count: " + str(len(res.history)) + \
                        ", response length:" + str(len(res.text)))
                res.encoding = self.encoding
                self._content=res.text
                logger.debug(type(res.text))
                logger.debug(res.text)
                self.redirect_count=len(res.history)

    def __content__(self):
        if not self._content:
            self.fetch(self.url)
        return self._content

    def __document__(self):
        if not self._document:
            self._document = PyQuery(self.content)
        return self._document

    def __links__(self):
        if self._links==None:
            lk=[]
            urls = [a.attr("href") for a in self.find("a[href]").items() \
                        if not a.attr("href").startswith("#") ]
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
            yield ("data",self._data)
        return iterator()


    def __getattr__(self,k):
        if k== "content":
            return self.__content__()
        elif k == "links":
            return self.__links__()
        elif k == "body":
            return self.find("body")
        elif k == "query":
            return parse_qs(self.splited_url.query)
        elif k in ["scheme","path","netloc"]:
            return getattr(self.splited_url,k)
        else:
            super(ContentProxy,self).__getattr__(k)

    def find(self,qstr):
        return self.__document__().find(qstr)

    def data(self,k,v):
        if isinstance(v,str): v= v.strip()
        self._data[k] = v

    def log(self,string):
        logger.info(string)


class Crawler(object):
    def __init__(self,debug = False):
        super(Crawler, self).__init__()
        self.fetched_urls = set()
        self.fetch_queue = deque()
        self.save_queue = []
        self.handlers = {}
        self.interval = 1
        self._default_handler = None
        self._save_handler = None
        self._debug_save_handler = None
        self._timerecord={}
        if debug : logging.basicConfig(level=logging.DEBUG)
        self._debug = debug

    def __call_handler(self,handler,proxy):
        tr = self._timerecord.get(proxy.splited_url.netloc)
        if tr and (time.time()-tr) < self.interval:
            logger.info("fetch frequency control: " + proxy.splited_url.netloc)
            self.__random_sleep()
            if not proxy.url in self.fetched_urls:
                self.append_to_fetched_urls([proxy.url,])
            return False
        else:
            ret = handler(proxy)
            if ret:
                self._timerecord[proxy.splited_url.netloc] = time.time()
            return ret

    def __random_sleep(self):
        delay = self.interval + random.random() * 10
        gevent.sleep(delay)

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

    def handler_for(self,subdomain,domain,force_https=False,interval=0):
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
        if handler:
            logger.info("processing url: "+url)
            if self.__call_handler(handler,proxy):
                self.append_to_fetch_queue(proxy.links)
                self.append_to_save_queue(proxy)
                self.append_to_fetched_urls([proxy.url,])
        else:
            logger.warn("no handler for url : " + proxy.url)

    def append_to_fetch_queue(self,urls):
        if len(self.fetched_urls)< __MAX_FETCH_QUEUE_CAPACITY__:
            self.fetch_queue.extend(urls)

    def append_to_save_queue(self,proxy):
        obj = dict(proxy)
        if obj.get('data'):
            self.save_queue.append(obj)
        if len(self.save_queue) > 200:
            self.save()

    def append_to_fetched_urls(self,urls):
        if len(self.fetch_queue)>__MAX_FETCHED_URLS_CAPACITY__:
            self.fetched_urls.clear()
        self.fetched_urls.update(urls)

    def save_handler(self,fn):
        self._save_handler = fn
        return fn

    def debug_save_handler(self,fn):
        self._debug_save_handler = fn
        return fn

    def save(self):
        logger.info("saving: save queue length: " + str(len(self.save_queue)))
        if self._save_handler and self.save_queue:
            to_save = self.save_queue
            self.save_queue=[]
            if self._debug:
                self._debug_save_handler(to_save)
            else:
                self._save_handler(to_save)

    def crawl(self):
        if self.fetch_queue:
            url = self.fetch_queue.popleft()
            try:
                self.process(url)
            except Exception, e:
                logger.error("crawl <%s> failed,error: %s" %(url,str(e)))
        else:
            self.__random_sleep()

    def repeat_crawl(self,worker_number = None):
        while True:
            if worker_number!=None:
                logger.info("worker %d starts crawl" % worker_number)
            self.crawl()

    def spawn(self,worker=5):
        gevent.signal(signal.SIGTERM,self.exit)
        workers = [gevent.spawn(self.repeat_crawl,i) for i in range(worker)]
        try:
            gevent.joinall(workers)
        except KeyboardInterrupt:
            logger.info("shuting down...")
            gevent.killall(workers)
            self.save()
            sys.exit(0)
            
    def exit(self):
        raise KeyboardInterrupt()

