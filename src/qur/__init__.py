##
# @file __init__.py
# @brief A full text search engine with python and mongo
# @author U{Chase.Zhang<mailto:chase.zhang@diumoo.net}
# @date 2013-04-19





import math,re
from pymongo import DESCENDING
__VERSION__ = (0,1)
__IGNORED_EN_WORDS__ = set(['the','of','to','and','a','in','is','it',''])
__EN_WORD_CUT__ = re.compile(r"\W*")
__CN_WORD_CUT__ = re.compile(ur"[^\u4E00-\u9FA5a-zA-Z0-9+#]*")


def versionstring():
    return '.'.join(__VERSION__)


class Qur(object):
    def __init__(self, db, name="",jieba_word_cut=False):
        super(Qur, self).__init__()
        self.db        = db

        self.words     = db["qur_%s_words" % name]

        datac          = db["qur_%s_relations" % data]
        self.data      = datac.find_one()
        if self.data == None:
            import datetime
            datac.insert({
                "texts_count":0,
                "qur_version": version(),
                "created_at": datetime.datetime.utcnow(),
                })
            self.data = datac.find_one()

        if jieba_word_cut:
            import jieba
            self.jieba = jieba
        else:
            self.jieba = None

    def indexText(self,entry,text):
        pass

    def seperateWords(self,text):
        text = test.lower().strip()
        if self.jieba:
            sentences=__EN_WORD_CUT__.split(unicode(text))
            words=[]
            for s in sentences:
                for w in jieba.cut(s):
                    words.append(w)
            return words
        else:
            words = __EN_WORD_CUT__.split(text)
            return words

    def calculateWordScore(self,words):
        wordsdict = {}
        for w in words:
            if w in __IGNORED_EN_WORDS__ : 
                continue
            elif wordsdict.get(w):
                wordsdict[w]+=1
            else:
                wordsdict[w] = 1
        maxfreq = max(wordsdict.values())
        return [(k,float(v)/maxfreq) for k,v in wordsdict.iteritems()]

