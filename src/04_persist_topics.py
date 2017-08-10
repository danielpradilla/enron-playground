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
topics = db.topics
authortopics = db.authortopics


def generate_topics(model,num_topics,num_words,topic_names):
    #build a collection of topics based on the model
    db_records = get_topic_words(model,num_topics,num_words)
    for i, db_record in enumerate(db_records):
        db_record['description'] = topic_names[i]
    #print db_records
    topics.drop()
    object_ids = topics.insert_many(db_records, ordered=False).inserted_ids

    return object_ids

def get_topic_words(model,num_topics,num_words):
    rtn = []
    i=0
    for topic in model.show_topics(num_topics,num_words):
        topic_dict = dict()
        topic_dict['name'] = "topic%s" % i
        topic_dict['nodes'] = []
        for word, probability in model.show_topic(topic[0]):
            node = dict()
            node['name'] = word
            node['value'] = probability
            topic_dict['nodes'].append(node)
        i+=1
        rtn.append(topic_dict)
    return rtn
              
def print_topics(model,num_topics,num_words):
    i=0
    for topic in model.show_topics(num_topics,num_words):
        words = ''
        for word, probability in model.show_topic(topic[0]):
            words += word + ' '
        i+=1
        print("Topic %s Words: %s" % (i, words))

        

def get_authors():
    rtn = dict()
    pipeline=[
        {"$group":{"_id":"$from","count":{"$sum":1}}}
    ]
    rtn = list(messageswords.aggregate(pipeline, allowDiskUse=True))
    return rtn

def generate_author_topics(model):
    author_topics = []
    r = re.compile('<.*')
    for author in get_authors():
        record = dict()
        record['from'] = author['_id']
        record['count'] = author['count']
        try:
            for topictuple in model.get_author_topics(author['_id']):
                record['topic'+str(topictuple[0])] = topictuple[1]
            author_topics.append(record)
        except:
            pass
    #print author_topics
    
    authortopics.drop()
    object_ids = authortopics.insert_many(author_topics, ordered=False).inserted_ids
    
    return object_ids


def main():
    start_time = time.time()
    dictionary_file = '../gensim/at/dictionary'
    model_file = '../gensim/at/model'
    num_topics=10
    num_words=10
    topic_names = ['Corporate','IT Services', 'Investor Market', 'e-commerce', 'Scheduling', 'Planning', 'Sports', 'Contracts', 'Headquarters', 'California']
    
    if not os.path.isfile(dictionary_file) or not os.path.isfile(model_file):
        return

    model = gensim.models.AuthorTopicModel.load(model_file)

    generate_topics(model,num_topics,num_words,topic_names)

    print_topics(model,num_topics,num_words)

    generate_author_topics(model)

    print("---done %s seconds ---" % (time.time() - start_time))
    
main()
