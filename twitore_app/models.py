#twitore models

import json
import datetime 

# mongo
from mongoengine import *
connect('twitore_dev')

# MongoDB
class MongoTweet(DynamicDocument):
	id = StringField(primary_key=True)
	collection = StringField()
