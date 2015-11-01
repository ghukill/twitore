#twitore models

import json
import datetime 

import localConfig

# mongo
from mongoengine import *
connect('twitore_dev')


# Tweet
class MongoTweet(DynamicDocument):
	id = StringField(primary_key=True)


# Collection
class Collection(DynamicDocument):
	name = StringField(primary_key=True)
	search_terms = ListField(StringField())
	minute_frequency = IntField() # consider adding minimum here


