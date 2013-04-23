# Qur
Qur is a fulltext simple search engine with python and mongodb, it support both English and Chinese. Although futher development is still needed, but the current release v0.1 has already provide basic search and sort function.

Test and feedback is welcome.

Qur 是一个利用Python和Mongodb完成的全文检索殷勤，支持英文和中文。此项目还需要进一步的开发，但是目前的v0.1版本已经提供了基本的搜索和排序功能。

欢迎测试和反馈

**version 0.1**

# Installation
Temporarily the only way to install qur is clone this repo by git and cp src/qur folder into your project folder.

暂时只能通过clone这个仓库的代码并把src里的qur文件夹拷贝到您项目的目录下来安装Qur.

# Basic usage

## GenericIndexer

You can use GenericIndexer to make index for a text, an entry id should be provided as the id of this text. Current version do not save the text itself, it only make index for the text and save a pointer to the entry id. When the text is matched in a search, the entry id is returned.

您可以使用 GenericIndexer 为一篇文章索引，您需要为这段文字指定一个entry id，目前的版本不会自己保存文本，它只会为文本制作索引并保存一个指向entry id的指针。当这篇文章在搜索中被匹配后，对应的entry id将会被返回。

example:

    import qur
    
    # create an indexer instance 创建一个索引对象
    #
    # the param db stands for an instance
    # of pymongo's database
    # the second parm specify name for index related
    # collection's name in mongodb
    # 参数 db 代表一个指定的 pymongo 数据库对象 
    # 第二个参数代表为索引相关集合指定的名称
    indexer = qur.GenericIndexer(db,"test") 

    # index a block of text 索引一篇文字
    indexer.indexText(entry_id,text)

## GenericSearcher

GenericSearcher is for searching. The initial function accepts the same parms as GenericIndexer. Make sure you gives a searcher the same parms as the indexer or it will fail to give results. 

GenericSearcher 用来搜索，其构造函数接受与GenericIndexer相同的参数，您应该给搜索器传入索引器相同的参数，否则它将无法返回搜索结果。

example:

    import qur
    searcher = qur.GenericIndexer(db,"test")
    
    searcher.search("a search string")



See py files in test folder.
请参考test文件夹下的py文件。


## Chinese support
Qur use [jieba](https://github.com/fxsjy/jieba) as Chinese word cut engine , to enable Chinese index and search function, just import jieba and pass it as the 3rd parm when initialize indexer and searcher

Qur 使用[jieba](https://github.com/fxsjy/jieba)作为中文分词引擎，激活中文索引和搜索功能，请导入jieba模块并将其作为初始化索引器和搜索器的第三个参数。

example:

    import qur,jieba

    indexer  = qur.GenericIndexer(db,"test",jieba)
    searcher = qur.GenericSearcher(db,"test",jieba)
 
# LICENCE
see LICENCE file
