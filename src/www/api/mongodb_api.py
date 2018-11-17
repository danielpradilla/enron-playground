import pymongo
import time
import string
import re
import os
import json
from bson import json_util

MongoClient = pymongo.MongoClient
conn = MongoClient('mongo-enron', 27017)
#use enron database
db = conn['enron']
messages = db.messages
messageswords = db.messageswords
topics = db.topics
authortopics = db.authortopics


def get_topics():
    rows = topics.find()
    rtn = build_json_response(rows)
    #print rtn
    return rtn

def get_author_topics(topicname):
    print(topicname)
    rows = authortopics.find({}).sort([(topicname, -1)]).limit(9)
    rtn = build_json_response(rows)
    return rtn

def get_message(id):
    rows = messages.find({"message-id":id},{"message-id":1, "body":1, "filename":1, "from":1, "x-from":1, "date":1, "to":1, "subject":1})
    rtn = build_json_response(rows)
    return rtn

def get_message_list(author):
    pipeline = [
        {"$match": {"from": author}},
        { "$match": {"spacy": {"$exists": True}}}, #select only the ones with entities
        {"$project":{"from":1, "message-id":1, "spacy.tokens":1, "spacyLength":{"$size":"$spacy"}}},
        {"$match": {"spacyLength": {"$gt": 2}}}, 
        {"$lookup":{"from": "messages", "localField": "message-id", "foreignField": "message-id","as": "message"}},
        {"$unwind": "$message"},
        {"$project": {"body":"$message.body", "from": "$from", "message-id": "$message-id", "date": "$message.date", "subject": "$message.subject"}},
        { "$sample": { "size": 10 } }
    ]
    rows = list(messageswords.aggregate(pipeline, allowDiskUse=True))
    rtn = build_json_response(rows)
    #print rtn
    return rtn
    
def build_json_response(response):
    rtn = json.dumps(list(response),  default=json_util.default)
    return rtn
