import spacy
import pymongo
import time
import random
import string
import re

from Queue import Queue
from threading import Thread




MongoClient = pymongo.MongoClient
conn = MongoClient('localhost', 27017)
#use enron database
db = conn['enron']
messages = db.messages

nlp = spacy.load('en_default')
batch_size=1000

def get_records(query):
    #returns results from query 
    rows = messages.find(query)
    rtn = rows
    # rtn = [rows[random.randrange(rows.count())] for item in range(limit)]
    return rtn


def sanitize_entity_text(text):
    #awful series of hacks for sanitizing edge cases
    rtn = text
    for char in ["\n", "\r", "\t", '"', "|", "}", "~", "v", ">", "&nbsp;", "_", "+"]:
        rtn = rtn.replace(char,"")
    #remove non-ascii characters
    rtn = ''.join([i if ord(i) < 128 else ' ' for i in rtn])
    #remove everything that looks like a date
    rtn = re.sub('\d{2}:\d{2}(:\d{2})?', ' ', rtn)
    rtn = re.sub('\d{2}\/\d{2}\/\d{2,4}', ' ', rtn)
    #remove stop words and strip unwanted starting characters
    stop_words =["a","an","the","in", ".", ",","",'"',"w/","y","you","your"]
    rtn = ' '.join([word.strip("\n\r\t-.\/,_;:!?/`'()[]=@,$*&+<> ") for word in rtn.split(" ") if word.lower() not in stop_words])
    return rtn

def remove_unwanted_entities(entities):
    unwanted_entities = [
        re.compile('\w+@'),
        re.compile('\s?Enron', re.I)
    ]
    rtn = [entity for entity in entities if not any(unwanted_entity.match(entity) for unwanted_entity in unwanted_entities)]
    return rtn

def sanitize_text(text):
    rtn = text
    #remove all kinds of whitespace
    rtn = re.sub('\s', ' ', rtn)
    return rtn

def extract_entities(doc):
    #https://spacy.io/docs/usage/entity-recognition
    #wanted_entities = ["NORP","FACILITY","ORG","GPE","LOC","PRODUCT"]
    wanted_entities = ["NORP", "FACILITY", "ORG", "PRODUCT"]
    entities = doc.ents
    #rtn = [(entity.text.replace('\n','').replace('\r','').replace('\t',''), entity.label_) for entity in entities if entity.label_ in wanted_entities]
    rtn = [sanitize_entity_text(entity.text) for entity in entities if entity.label_ in wanted_entities]

    rtn = remove_unwanted_entities(rtn)
    rtn = set(rtn)
    #print rtn
    return rtn

def extract_tokens(doc):
    #build a list of words
    #https://spacy.io/docs/api/token
    #use the lemmatizer, only consider words which are alphabetical and larger than 2 characters
    rtn = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha and len(token.lemma_)>2]
    return rtn

def get_nlp_dict(db_record):
    #builds a dictionary of nlp items to later insert alongside the document
    #print '-----------'
    rtn = {"entities":set(), "tokens":set()}
    fields = ['body','subject']
    for field in fields:
        doc = nlp(sanitize_text(db_record[field]))
        rtn["entities"].update(extract_entities(doc))
        rtn["tokens"].update(extract_tokens(doc))

    #convert to list, otherwise i wont be able to insert
    for key in rtn:
        rtn[key] = list(rtn[key])
    return rtn

def update_record(db_record, nlp_dict):
    # if (len(nlp_dict['entities']))>0:
    messages.update_one({"_id": db_record["_id"]},{"$set":{"spacy":nlp_dict}})


def process_record_queue(queue):
    start_time = time.time()
    i=0
    while True:
        db_record = queue.get()
        nlp_dict = get_nlp_dict(db_record)
        update_record(db_record, nlp_dict)
        #print db_record
        i+=1
        if i % batch_size == 0:
            print "%s - _id:%s = [%s] - %s seconds" % (i, db_record["_id"], nlp_dict, (time.time() - start_time))
        queue.task_done()

def main():
    start_time = time.time()
    i=0
    query = {"date":{"$regex": "2000"}, "body":{"$ne": ""}}
    query = {"body":{"$ne": ""}}
    db_records = get_records(query)
    for db_record in db_records:
        nlp_dict = get_nlp_dict(db_record)
        update_record(db_record, nlp_dict)
        #print db_record
        i+=1
        if i % batch_size == 0:
            print "%s - _id:%s = [%s] - %s seconds" % (i, db_record["_id"], nlp_dict, (time.time() - start_time))
    print("---main %s seconds ---" % (time.time() - start_time))

def main_mt():
    start_time = time.time()
    query = {"date":{"$regex": "2000"}, "body":{"$ne": ""}}
    query = {"body":{"$ne": ""}}
    queue = Queue(maxsize=0)
    num_threads = 10

    db_records = get_records(query)
    map(queue.put, db_records)    

    for i in range(num_threads):
        worker = Thread(target=process_record_queue, args=(queue,))
        worker.setDaemon(True)
        worker.start()


    queue.join()
    print("---main %s seconds ---" % (time.time() - start_time))

main_mt()