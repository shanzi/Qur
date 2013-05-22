import os,sys,unittest
sys.path.append(os.path.join(os.path.dirname(__file__),"../src/"))


import qur
import jieba
from pymongo import mongo_client

class TestIndexSeq(unittest.TestCase):
    def setUp(self):
        client = mongo_client.MongoClient()
        self.db = client["test_database"]
        self.entries = self.db.entries
        self.indexer = qur.GenericIndexer(
                self.db,
                name="test",
                word_cut=jieba)

        self.articles=[]
        for p in os.listdir("articles"):
            p = os.path.join("articles",p)
            f=open(p)
            self.articles.append((p,f.read()))
            f.close()

        self.indexer.clearData()
        self.entries.drop()

    def test_index(self):

        for p,s in self.articles:
            _id = self.entries.insert({"filename":p})
            self.indexer.indexText( _id , s)


        self.assertTrue(self.indexer.words.count()>0)
        self.assertTrue(self.indexer.relations.count()>0)

    
if __name__=="__main__":
    unittest.main()
