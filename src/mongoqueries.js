

db.messages.aggregate([
//  {"$match":{"spacy.entities":"East Power Trading"}},
  {"$project":{"from":1, "spacy.entities":1}}, 
  {"$unwind": "$spacy.entities"}, 
  {"$match":{"spacy.entities":{"$ne":""}}},
  {"$match":{"spacy.entities":{"$nin":["Enron","Houston","Texas"]}}},
  {"$group": {
    "_id":{"from":"$from","entity":"$spacy.entities"}, 
    "individualFreq":{"$sum":1}
    }
  },
  {"$group": {
    "_id":"$_id.entity", 
    "total":{"$sum":"$individualFreq"},
        "from": {
              "$push": {
                "from": "$_id.from",
                "individualFreq": "$individualFreq"
              }
            }
    }
  },
    { "$unwind": "$from" },
    { "$project": {
        "_id":{
                "entity":"$_id",
                "from": "$from.from"
        },
        "individualFreq": "$from.individualFreq",
        "pct": {
              "$divide": [ "$from.individualFreq", "$total" ] 
        },
        "total":{"$multiply":[ 1, "$total"]}
        }
     },
     {"$sort":{"total":-1,"pct":-1}}
    ,{"$out":"entitiesSummary"}
],{allowDiskUse: true}
)   

/
db.messages.aggregate(
    {"$project":{"spacy.tokens":1, "spacy.entities":1}}
)
/
db.messages.find({},{"spacy.tokens":1, "spacy.entities":1})
/

[
  {$match: {author: {$ne: 1}}},
  {$limit: 10000},
  {$group: {
    _id: 1,
    book: {$push: {title: '$title', author: '$author', copies: '$copies'}}
  }},
  {$unwind: {path: 'book', includeArrayIndex: 'rownum'}},
  {$project: {
    author: '$book.author',
    title: '$book.title',
    copies: '$book.copies',
    rownum: 1
  }}
]
  
  
db.messages.aggregate([
  { "$match": {"spacy.tokens":{"$exists":true}}},
  { "$project": {
    "idOrig": "$_id",
    "message-id": "$message-id",
    "from": "$from",
    "spacy": { "$concatArrays": [ "$spacy.tokens", "$spacy.entities" ] }
  }},
  { "$sort": {"message-id":1}},
  {"$group": {
    "_id": 1,
    "document": {"$push": {"idOrig": "$idOrig", "message-id": "$message-id", "from": "$from", "spacy": "$spacy"}}
  }},
  {"$unwind": {"path": "$document", "includeArrayIndex": 'rownum'}},
  {"$project": {
    "_id": "$document.idOrig",
    "message-id": '$document.message-id',
    "from": '$document.from',
    "spacy": '$document.spacy',
    "rownum": 1
  }},
  {"$group":{
     "_id":"$from",
     "documents":{"$push": "$rownum"}  
    }
  },
  { "$sample": { "size": 10 } }
//  ,{"$out":"messagesWords"}
],{allowDiskUse: true}
)
/








db.messages.aggregate([
  { "$match": {"spacy.tokens":{"$exists":true}}},
  { "$project": {
    "idOrig": "$_id",
    "message-id": "$message-id",
    "from": "$from",
    "spacy": { "$concatArrays": [ "$spacy.tokens", "$spacy.entities" ] }
  }},
  {"$group": {
    "_id":"$from",
     "document":{"$push":{"idOrig": "$idOrig", "message-id": "$message-id", "from": "$from", "spacy": "$spacy"}},
     "count":{"$sum":1}
    }
  },
  { "$match": {"count":{"$gt":2}}},
  {"$unwind": "$document"},
  {"$project": {
    "_id": "$document.idOrig",
    "message-id": '$document.message-id',
    "from": '$document.from',
    "spacy": '$document.spacy',
    "rownum": 1
  }},

  { "$sort": {"message-id":1}},
  {"$group": {
    "_id": 1,
    "document": {"$push": {"idOrig": "$idOrig", "message-id": "$message-id", "from": "$from", "spacy": "$spacy"}}
  }},
  {"$unwind": {"path": "$document", "includeArrayIndex": 'rownum'}},
  {"$project": {
    "_id": "$document.idOrig",
    "message-id": '$document.message-id',
    "from": '$document.from',
    "spacy": '$document.spacy',
    "rownum": 1
  }},
  {"$group":{
     "_id":"$from",
     "documents":{"$push": "$rownum"}  
    }
  }
],{allowDiskUse: true}
)

/


//JOIN
db.messageswords.aggregate(
    {"$match": {"from": "40enron@enron.com"}},
    {"$lookup":{"from": "messages", "localField": "message-id", "foreignField": "message-id","as": "message"}},
    {"$unwind": "$message"},
    {"$project": {"body":"$message.body", "from": "$from", "message-id": "$message-id", "date": "$message.date", "subject": "$message.subject"}}
    
)



/

db.messages.find({"date":/2000/, "body":{"$ne": ""}})
/



db.messages.aggregate([
{ "$match": {"spacy.tokens":{"$exists":true}}}, 
{ "$project": {"idOrig": "$_id", "message-id": "$message-id","from": "$from","spacy": "$spacy.tokens" }}, 

{"$group": { "_id":"$from", "document":{"$push":{"idOrig": "$idOrig", "message-id": "$message-id", "from": "$from", "spacy": "$spacy"}}, "count":{"$sum":1} }}, 


{"$unwind": "$document"}, 
{"$project": {"_id": "$document.idOrig","message-id": '$document.message-id',"from": '$document.from',"spacy": "$document.spacy"}}, 

{ "$sort": {"message-id":1}}, 
{"$group": {"_id": 1,"document": {"$push": {"idOrig": "$idOrig", "message-id": "$message-id", "from": "$from", "spacy": "$spacy"}}}}, 
{"$unwind": {"path": "$document", "includeArrayIndex": "rownum"}}, 
{"$project": {"_id": "$document.idOrig","message-id": "$document.message-id","from": "$document.from","spacy": "$document.spacy","rownum": 1}}
],{allowDiskUse: true}
)



//db.messages.remove({})

/

