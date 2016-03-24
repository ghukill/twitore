#twitore models

import json
import datetime 

import localConfig


# using flask mongo integreation
from twitore_app import db

# Tweet
class MongoTweet(db.DynamicDocument):
	id = db.StringField(primary_key=True)


# Collection
class Collection(db.DynamicDocument):
	name = db.StringField(primary_key=True)
	search_terms = db.ListField(db.StringField())
	minute_frequency = db.IntField() # consider adding minimum here


