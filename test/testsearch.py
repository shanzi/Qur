import os,sys,unittest,readline
sys.path.append(os.path.join(os.path.dirname(__file__),"../src/"))

import qur
from pymongo import mongo_client
import jieba

def test_search():
    client = mongo_client.MongoClient()
    db = client["test_database"]
    searcher = qur.GenericSearcher(
            db,
            name="test",
            word_cut=jieba
            )
    readline.parse_and_bind("")
    for i in range(10):
        print "search test:"
        string = raw_input("> ")
        res = searcher.search(string)
        if res:
            print '-'*80
            for r in res:
                entry_id=r["_id"]["entry_id"]
                entry = db.entries.find_one(entry_id)
                print "%2.5f %s" % (r["score"] , entry["filename"])
                print "Matched Words: ",", ".join(r["matched_words"])
                print ""

if __name__=="__main__":
    test_search()
