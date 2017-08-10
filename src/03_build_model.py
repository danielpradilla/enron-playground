import pymongo
import time
import random
import string
import re
import os
import gensim


MongoClient = pymongo.MongoClient
conn = MongoClient('localhost', 27017)
#use enron database
db = conn['enron']
messages = db.messages
messageswords = db.messageswords


def generate_messagewords(sample_size):
    #agregate the spacy tokens and generate a summary collection

    #query for LDA
    # pipeline=[
    #     { "$match": {"spacy.entities":{"$exists":True}}},
    #     { "$project": {"idOrig": "$_id", "message-id": "$message-id","from": "$from","spacy": "$spacy.tokens" }},
    #     {"$out":"messageswords"}
    # ]

    #query for Author-topic
    #horrible aggregation with the aim to create a numbered list of documents, sorted by message-id. rownum will contain numbers from 0 to n
    pipeline=[
        { "$match": {"spacy.entities": {"$exists": True}}}, #select only the ones with entities
        { "$match": {"spacy.entities": {"$not": {"$size": 0}}}},  #select only the ones with entities
        { "$match": {"spacy.tokens": {"$not": {"$size": 0}}}},  #select only the ones with tokens
        #{ "$sample": { "size": sample_size } },
        #{ "$match":{"from":re.compile("^[a-z].*")}},
        #{ "$project": {"idOrig": "$_id", "message-id": "$message-id","from": "$from","spacy": { "$concatArrays": [ "$spacy.tokens", "$spacy.entities" ] } }}, #concatenate arrays
        { "$project": {"idOrig": "$_id", "message-id": "$message-id","from": "$from","spacy": "$spacy.tokens" }}, 

        {"$group": { "_id":"$from", "document":{"$push":{"idOrig": "$idOrig", "message-id": "$message-id", "from": "$from", "spacy": "$spacy"}}, "count":{"$sum":1} }}, #wind up the document per author and count documents per author
        #{ "$match": {"count":{"$gt":100}}}, #select only the authors with more than 100 documents
        #{ "$match": {"count":{"$lt":1000}}}, #select only the authors with less than 1000 documents
        {"$unwind": "$document"}, #unwind the grouping by author
        {"$project": {"_id": "$document.idOrig","message-id": '$document.message-id',"from": '$document.from',"spacy": "$document.spacy"}}, #project the fields again

        { "$sort": {"message-id":1}}, #sort by message-id
        {"$group": {"_id": 1,"document": {"$push": {"idOrig": "$idOrig", "message-id": "$message-id", "from": "$from", "spacy": "$spacy"}}}}, #wind up all the documents in order to create the rowcount
        {"$unwind": {"path": "$document", "includeArrayIndex": "rownum"}}, #add the rownum field
        {"$project": {"_id": "$document.idOrig","message-id": "$document.message-id","from": "$document.from","spacy": "$document.spacy","rownum": 1}}, #project the rownum field
        {"$out": "messageswords"}  #save it in a new collection
    ]
    messages.aggregate(pipeline, allowDiskUse=True)
    return True

def get_words():
    rows = messageswords.find()
    rtn = [row['spacy'] for row in rows]
    return rtn

def get_author_docs():
    rtn = dict()
    pipeline=[
      {"$group":{"_id":"$from","documents":{"$push": "$rownum"} } }
    ]
    rows = list(messageswords.aggregate(pipeline, allowDiskUse=True))
    for author in rows:
        rtn[str(author['_id'])] = [int(document) for document in author['documents']]
    return rtn

def get_dictionary(records):
    #http://radimrehurek.com/gensim/corpora/dictionary.html
    rtn = gensim.corpora.Dictionary(records)
    
    no_below = 5 #filter out words that appear x times or less
    no_above = 0.5 #filter out words that appear more than y of the time
    #using the defaults according to the doc
    rtn.filter_extremes(no_below=no_below, no_above=no_above)
    return rtn

def get_corpus(dictionary, records):
    return [dictionary.doc2bow(record) for record in records]

def get_lda_model(dictionary, corpus, num_topics, passes):
    start_time = time.time()
    models = []
    model = gensim.models.ldamulticore.LdaMulticore(corpus, num_topics=num_topics, id2word=dictionary, passes=passes, random_state=1)
    #get the Umass topic coherence
    #http://radimrehurek.com/gensim/models/ldamodel.html#gensim.models.ldamodel.LdaModel.top_topics
    top_topics = model.top_topics(corpus)
    topic_score = sum([topic[1] for topic in top_topics])
    models.append((model, topic_score))
    print("--model done %s seconds. topic score %d ---" % (time.time() - start_time, topic_score))
    print_topics(model,num_topics)
    print("topic coherence score: %d" % topic_score)
    """
    topic coherence score: -3544
    Words: market provide time base cost year include risk company business 
    Words: gas lng oil natural shackleton contact canada sara crude LNG 
    Words: attach review information receive document request report change question date 
    Words: click email receive free send mail information service new web 
    Words: charlie checkout game football player team play league reports report 
    Words: thank know deal let power gas question price change day 
    Words: state energy california say power news report enpower industry utility 
    Words: thank know enron let work time meeting like group week 
    Words: fax enron phone houston thank north america smith street master 
    Words: good day time like get great come know think look 

    topic coherence score: -3479
    Topic 1 Words: market follow power time energy issue day enron report new 
    Topic 2 Words: thank meeting time new think good week information enron deal 
    Topic 3 Words: thank attach know let question agreement enron deal gas send 
    Topic 4 Words: time meeting think good day week want follow mail change 
    Topic 5 Words: gas click email information available market receive report view day 
    Topic 6 Words: thank know enron let time fax phone work good houston 
    Topic 7 Words: start date hour schedule hourahead award variance detect ancillary good 
    Topic 8 Words: thank enron follow question year attach information new help send 
    Topic 9 Words: new year company energy enron state plan buy york stock 
    Topic 10 Words: click send receive mail email free message information time new 

    """
    return model  

def get_at_model(dictionary, corpus, author2doc, num_topics, passes):
    start_time = time.time()
    models = []
    model = gensim.models.atmodel.AuthorTopicModel(corpus, num_topics=num_topics, id2word=dictionary, author2doc=author2doc, passes=passes, random_state=1, chunksize=2000, eval_every=None, iterations=1)

    #get the Umass topic coherence
    #http://radimrehurek.com/gensim/models/ldamodel.html#gensim.models.ldamodel.LdaModel.top_topics
    top_topics = model.top_topics(corpus)
    topic_score = sum([topic[1] for topic in top_topics])
    models.append((model, topic_score))
    print("--model done %s seconds. topic score %d ---" % (time.time() - start_time, topic_score))
    print_topics(model,num_topics)
    print("topic coherence score: %d" % topic_score)
    """
    topic coherence score: -3204
    Topic 1 Words: click receive information free email send message offer available unsubscribe 
    Topic 2 Words: know thank think good let like want work look time 
    Topic 3 Words: start date time game schedule team play week calendar hour 
    Topic 4 Words: california jeff good ferc issue FERC market state Best energy 
    Topic 5 Words: thank enron attach fax know let agreement houston phone question 
    Topic 6 Words: week word world time new send research visit change today 
    Topic 7 Words: deal gas new price day month volume sell daily buy 
    Topic 8 Words: year new company provide write american benefit million money stock 
    Topic 9 Words: follow time meeting date report day information review question request 
    Topic 10 Words: dear contact question receive subject note account mail find area 
    """
    return model

def print_topics(model,num_topics):
    i=0
    for topic in model.show_topics(num_topics):
        words = ''
        for word, probability in model.show_topic(topic[0]):
            words += word + ' '
        i+=1
        print("Topic %s Words: %s" % (i, words))


def main():
    start_time = time.time()
    dictionary_file = '../gensim/at/dictionary'
    model_file = '../gensim/at/model'
    num_topics=10
    passes=2
    sample_size=500000
    
    if not os.path.isfile(dictionary_file) or not os.path.isfile(model_file):
        generate_messagewords(sample_size)
        records = get_words()
        author2doc = get_author_docs()
        print("---query done %s seconds ---" % (time.time() - start_time))
        dictionary = get_dictionary(records)
        dictionary.save(dictionary_file)
        print("--dictionary saved %s seconds ---" % (time.time() - start_time))
        corpus = get_corpus(dictionary, records)
        print("--corpus done %s seconds ---" % (time.time() - start_time))
        #model = get_lda_model(dictionary, corpus, num_topics, passes)
        model = get_at_model(dictionary, corpus, author2doc, num_topics, passes)
        model.save(model_file)
    else:
        dictionary = gensim.corpora.Dictionary.load(dictionary_file)
        #model = gensim.models.ldamodel.LdaModel.load(model_file)
        model = gensim.models.AuthorTopicModel.load(model_file)

    print_topics(model,num_topics)


    print("---done %s seconds ---" % (time.time() - start_time))
    
main()
