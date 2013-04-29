##
# @file __init__.py
# @brief a simple web crawler
# @author U{Chase.Zhang<mailto:chase.zhang@diumoo.net}
# @date 2013-04-26


from bs4 import BeautifulSoup
from urlparse import urlsplit,urljoin,urlunsplit
import requests,logging,re,time


logger = logging.getLogger("cra_crawler")
fh=logging.FileHandler("cra_crawler.log")
fh.setLevel(logging.DEBUG)


class Crawler(object):
    def __init__(self):
        super(Crawler, self).__init__()
        self.fetched = set()
        self.queue = []
        self.handlers = {}
        self.default_handler = None

    def get_handler_for(self,netloc):
        components=netloc.split(".")
        if len(components) <2: return None
        for i in range(len(components)-2):
            subdomain = '.'.join(components[:i])
            domain = '.'.join(components[i:])
            dhandler = self.handlers.get(domain)
            if dhandler:
                subh = dhandler.get(subdomain)
                if subh: return subh
                elif dhandler.get('*'):
                    return dhandler.get('*')
        return self.default_handler

    def handler_for(self,subdomains,domain,force_https=False,handler):
        if not subdomains: subdomains = ['',]
        if isinstance(subdomains,str): 
            subdomains = [subdomains,]
        for subdomain in subdomains:
            self.handlers[domain][subdomain] = handler

    def default_handler(self,func):
        self.default_handler = func

    def split_url(self,url):
        o = urlsplit(url)
        return (o.scheme,o.netloc,o.path,o.query)

    def fetch(self,url):
        logger.info("fetching url: " + url)
        res=requests.get(url,timeout=10)
        if res.status_code == 200:
            return r.text,len(res.history)
        return None,0



