##
# @file __init__.py
# @brief A full text search engine with python and mongo
# @author U{Chase.Zhang<mailto:chase.zhang@diumoo.net}
# @date 2013-04-19





import math,re,ignorewords
from bson.code import Code

__VERSION__ = (0,1)
__EN_WORD_CUT__ = re.compile(r"\W*")
__WORD_MIN_SCORE__ = 0.001
__SEARCH_WORDS_LIMIT__ = 3


def versionstring():
    return '.'.join(__VERSION__)

class DBStruct:
    def __init__(self, db,name):
        self.db        = db
        self.words     = db["qur_%s_words"     % name]
        self.relations = db["qur_%s_relations" % name]
        self.ensureIndex()

    def ensureIndex(self):
        self.words.ensure_index({"word":1,"freq":1})
        self.relations.ensure_index({"word":1,"score":-1})
        self.relations.ensure_index({"entry_id":1,"score":-1})

class GenericIndexer(DBStruct):
    def __init__(self, db, name="",word_cut=False):
        super(DBStruct, self).__init__(db,name)

        self.word_cut = word_cut

    def indexText(self,entry_id,text):
        words = self.seperateWords(text)
        scores = self.calculateWordScore(words)
        inserts =[]
        for w,s in scores:
            self.words.update(
                    {"word":w},
                    {"$inc":{"freq":1}},
                    False,True)
            inserts.append(
                    {"word":w,"score":s,"entry_id":entry_id})

        self.relations.insert(inserts)
        self.data

    def seperateWords(self,text):
        text = test.lower().strip()
        if self.word_cut:
            sentences=__EN_WORD_CUT__.split(unicode(text))
            words=[]
            for s in sentences:
                for w in word_cut.cut(s):
                    words.append(w)
            return words
        else:
            words = __EN_WORD_CUT__.split(text)
            return words

    def calculateWordScore(self,words):
        wordsdict = {}
        for w in words:
            if w and len(w) > 20 :
                continue
            elif w in ignorewords.EN:
                continue
            elif self.word_cut and w in ignorewords.CN:
                continue
            elif wordsdict.get(w):
                wordsdict[w]+=1
            else:
                wordsdict[w] = 1

        maxfreq = float(max(wordsdict.values()))
        ret = []
        for k,freq in wordsdict.iteritems():
            s=freq/maxfreq
            if s < __WORD_MIN_SCORE__:
                del wordsdict[k]
            else:
                ret.append((k,s))
        return ret 

class GenericSearcher(DBStruct):
    def __init__(self,db,name):
        super(DBStruct, self).__init__(db,name,word_cut)
        self.word_cut = word_cut

    def processSearchString(self,searchstring):
        if word_cut:
            words = word_cut.cut(searchstring)
        else:
            words = __EN_WORD_CUT__.split(searchstring)
        ws    = self.words.find({"word":{"$in":words}}).sort({"freq":1})
        query = [ws.next()["word"] for x in range(__SEARCH_WORDS_LIMIT__)]
        ret   = this.relations.aggregate(
                {"$match":{"word":{"$in":query}}},
                {"$group":{
                    "_id":{"entry_id":"$entry_id"},
                    "score":{"$sum":"$score"},
                    "matched_words":{"$addToSet":"$word"}
                    }},
                {"$limit":100},
                {"$sort":{"score":-1}});
        if ret[ok]:
            return ret["result"]
        else:
            return None
            


