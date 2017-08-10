import os
import email
import re
import pymongo
import time
from bs4 import BeautifulSoup
import warnings

root_dir = "../data/maildir"
batch_size = 3000


#mongo settings
#conn = MongoClient('mongo-enron', 27017)
MongoClient = pymongo.MongoClient
conn = MongoClient('localhost', 27017)
#use enron database
db = conn['enron']
messages = db.messages


warnings.filterwarnings("ignore", category=UserWarning, module='bs4')



#parsing settings
#if you find any of these strings, stop parsing. It is he end of the email
stop_regexes = [
    re.compile('----\s*Forwarded by'),
    re.compile('----\s*Original Message'),
    re.compile('_{20}'),
    re.compile('\*{20}'),
    re.compile('={20}'),
    re.compile('-{20}'),
    re.compile('\son \d{2}\/\d{2}\/\d{2,4} \d{2}:\d{2}:\d{2} (AM|PM)$', re.I),
    re.compile('\d{2}\/\d{2}\/\d{2,4} \d{2}:\d{2} (AM|PM)', re.I),
    re.compile('^\s?>?(From|To):\s?', re.I), 
    re.compile('LOG MESSAGES:',re.I),
    re.compile('=3D=3D',re.I),
    re.compile('Memo from.*on \d{2}\s(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?),', re.I),
    re.compile('Outlook Migration Team', re.I),
    re.compile('PERSON~', re.I),
    re.compile('>>>', re.I)
]



#mongo functions
def create_index():
	#let us build an arbitrary index to force the failure of seemingly-repeated emails 
    keyfields = [('from',pymongo.ASCENDING), ('subject',pymongo.ASCENDING), ('date',pymongo.ASCENDING)]
    messages.create_index(keyfields, unique=True)

    keyfields = [('message-id',pymongo.ASCENDING)]
    messages.create_index(keyfields, unique=True)

def upsert_record(db_record):
    #performs an upsert in order not to insert repeated emails
    keyfields = ['from', 'subject', 'date']
    key = {}
    for keyfield in keyfields:
    	if keyfield in db_record:
    		key[keyfield] = db_record[keyfield]
    object_id = db.messages.replace_one(key, db_record, True).upserted_id
    #print object_id
    return object_id


def insert_records(db_records):
    object_ids = []
    if len(db_records)>0:
        try:
            object_ids = messages.insert_many(db_records, ordered=False).inserted_ids
        except pymongo.errors.BulkWriteError as e:
            ##ignoring duplicates
            print "ignoring duplicates"
            other_errors = filter(lambda x: x['code'] != 11000, e.details['writeErrors'])
            if len(other_errors):
                print other_errors
            pass

        return object_ids



#parsing fnctions
def get_file_list():
	rtn = []
	i=0
	#rtn = [os.path.join(root, filename) for root, dirs, files in os.walk(root_dir, topdown=False) for filename in files ]
	for root, dirs, files in os.walk(root_dir,topdown=False):
	    for filename in files:
	        if not filename.startswith("."): 
	            path = os.path.join(root,filename)
	            rtn.append(path)
	            i+=1
	            if i % batch_size == 0:
	                print ("%s - %s" % (i, path) )
	return rtn
            
def get_msg_from_file(filename):
    #extract email message from a file
    with open(filename, "r") as f:
        contents = f.read()

    rtn = email.message_from_string(contents)
    return rtn

def apply_stop_regexes(body):
    #applies the regexes contained in the stop_regex_global
    rtn = ''
    #split the body of the message into lines
    for line in body.splitlines():
        #if we find one of the stop expressions, stop processing and return immediately
        for stop_regex in stop_regexes:
            if(stop_regex.search(line))!=None:
                return rtn
        rtn+=line
        #add the line breaks again
        rtn+='\n'
    return rtn

def convert_html(html):
	soup = BeautifulSoup(html)
	rtn = soup.get_text()
	return rtn

def translate_unwanted(body):
    #translates unwanted characters
    rtn = body
    unwanted = [("=20"," "),("=01,","'"),("=02",":"),("=09",":"),("=\n","\n"),("01=07"," ")]
    for (char, replacement) in unwanted:
        rtn = rtn.replace(char, replacement)
    return rtn


def sanitize_string(str):
	#performs several sanitations
	rtn = str
	rtn = convert_html(rtn)
	rtn = apply_stop_regexes(rtn)
	rtn = translate_unwanted(rtn)
	return rtn


def get_db_record_dict(msg, filename):
    rtn=dict()
    #these are the interesting fields to buid a schema
    fields=['Message-ID', 'Date', 'From', 'To', 'Cc', 'Bcc', 'Subject','X-From', 'X-To', 'X-cc', 'X-bcc']

    for field in fields:
        if field in msg:
            rtn[field.lower()] = msg[field].decode('ISO-8859-1').encode('utf-8')
            #in the case of destination emails, create a nice array
            if field in ('To', 'X-To', 'Cc', 'X-cc', 'Bcc', 'X-bcc'):
                rtn[field.lower()] = [to_str.strip('\n\r\t ') for to_str in rtn[field.lower()].split(",")]

    rtn['filename'] = filename.split("maildir/")[1]
    body = msg.get_payload()
    body = sanitize_string(body)
    rtn['body'] = body
    return rtn



def log_msg(msg):
    #prints out an email
    headers = msg.items()
    #print headers
    #print msg.keys()
    
    #these are the interesting fields to buid a schema
    fields=['Message-ID', 'Date', 'From', 'To', 'Cc', 'Bcc', 'Subject','X-From', 'X-To', 'X-cc', 'X-bcc']

    print '----metadata-----'
    for field in fields:
        if field in msg:
            print field + ':' + msg[field]

    body = msg.get_payload()
    print '----clean body-----'
    print apply_stop_regexes(body)
    print '----full body-----'
    print body


def process_file_list_bulk(file_list):
	start_time = time.time()
	db_records=[]
	i=0
	for filename in file_list:
		msg = get_msg_from_file(filename)
		db_record = get_db_record_dict(msg, filename)
		db_records.append(db_record)
		#batch insert
		if len(db_records) % batch_size == 0:
			insert_records(db_records)
			db_records=[]
			i+=batch_size
			print("---batch insert %s records, %s seconds accumulated ---" % (i, time.time() - start_time))

    #insert the leftovers
	insert_records(db_records)

	print("---finished insertion %s seconds ---" % (time.time() - start_time))



def main():
	start_time = time.time()
	file_list = get_file_list()
	create_index()
	process_file_list_bulk(file_list)
	print("---total execution %s seconds ---" % (time.time() - start_time))


main()