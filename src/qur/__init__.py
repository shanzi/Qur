##
# @file __init__.py
# @brief A full text search engine with python and mongo
# @author U{Chase.Zhang<mailto:chase.zhang@diumoo.net}
# @date 2013-04-19





import math,re,ignorewords
from bson.code import Code
from Stemmer import Stemmer

__VERSION__ = (0,1)
__EN_WORD_CUT__ = re.compile(r"[^a-zA-Z]*")
__CN_WORD_CUT__ = re.compile(ur"[^\u4E00-\u9FA5a-zA-Z0-9+#]+")
__WORD_MIN_SCORE__ = 0.001
__SEARCH_WORDS_LIMIT__ = 3
__STEMMER__ = Stemmer("english")


def versionstring():
    return '.'.join(__VERSION__)

class DBStruct(object):
    def __init__(self, db,name):
        super(DBStruct,self).__init__()
        self.db        = db
        self.words     = db["qur_%s_words"     % name]
        self.relations = db["qur_%s_relations" % name]
        self.ensureIndex()

    def ensureIndex(self):
        self.words.ensure_index([("word",1),("freq",1)])
        self.relations.ensure_index([ ("word",1),("score",-1) ])
        self.relations.ensure_index([("entry_id",1),("score",-1)])

    def clearData(self):
        self.words.drop()
        self.relations.drop()

class GenericIndexer(DBStruct):
    def __init__(self, db, name="",word_cut=None):
        super(GenericIndexer, self).__init__(db,name)

        self.word_cut = word_cut

    def indexText(self,entry_id,text):
        words = self.seperateWords(text)
        stemmed_words = __STEMMER__.stemWords(words)
        scores = self.calculateWordScore(stemed_words)
        inserts =[]
        for w,s in scores:
            self.words.update(
                    {"word":w},
                    {"$inc":{"freq":1}},
                    upsert=True)
            inserts.append(
                    {"word":w,"score":s,"entry_id":entry_id})

        self.relations.insert(inserts)

    def seperateWords(self,text):
        text = text.lower().strip()
        if self.word_cut:
            if isinstance(text,unicode):
                sentences=__CN_WORD_CUT__.split(text)
            else:
                sentences=__CN_WORD_CUT__.split(text.decode("utf8"))
            words=[]
            for s in sentences:
                for w in self.word_cut.cut(s):
                    words.append(w)
            return words
        else:
            words = __EN_WORD_CUT__.split(text)
            return words

    def calculateWordScore(self,words):
        wordsdict = {}
        for w in words:
            if not w:continue
            if len(w) > 20:
                continue
            elif w in ignorewords.EN:
                continue
            elif w in ignorewords.CN:
                continue
            elif wordsdict.get(w):
                wordsdict[w] +=1
            else:
                wordsdict[w] = 1

        maxfreq = float(max(wordsdict.values()))
        ret = []
        for k,freq in wordsdict.iteritems():
            s=freq/maxfreq
            if s > __WORD_MIN_SCORE__:
                ret.append((k,s))
        return ret 

class GenericSearcher(DBStruct):
    def __init__(self,db,name,word_cut=None):
        super(GenericSearcher, self).__init__(db,name)
        self.word_cut = word_cut

    def search(self,string):
        query = self.processSearchString(string)
        stemmed_query = __STEMMER__.stemWords(query)
        ret   = self.relations.aggregate(
                [{"$match":{"word":{"$in":stemmed_query}}},
                {"$group":{
                    "_id":{"entry_id":"$entry_id"},
                    "score":{"$sum":"$score"},
                    "matched_words":{"$addToSet":"$word"}
                    }},
                {"$sort":{"score":-1}},
                {"$limit":100}, ]);
        if ret["ok"]:
            return ret["result"]
        else:
            return None

    def processSearchString(self,searchstring):
        if self.word_cut:
            words = self.word_cut.cut(searchstring)
        else:
            words = __EN_WORD_CUT__.split(searchstring)
        ws    = list(self.words.find({"word":{"$in":list(words)}}).sort([("freq",1)]))
        return [x["word"] for x in ws[:__SEARCH_WORDS_LIMIT__]]
