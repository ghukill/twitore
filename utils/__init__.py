#!/usr/bin/env python

import os
import re
import sys
import json
import twarc
import logging

# imported first, b
import localConfig
from twitore_app import models,twarc_instance

"""
MODIFIED VERSION FROM TWARC'S UTILS

This little utility uses twarc to write Twitter search results to a directory
of your choosing. It will use the previous results to determine when to stop
searching.

So for example if you want to search for tweets mentioning "ferguson" you can 
run it:

	% twarc-archive.py ferguson /mnt/tweets/ferguson

The first time you run this it will search twitter for tweets matching 
"ferguson" and write them to a file:

	/mnt/tweets/ferguson/tweets-0001.json

When you run the exact same command again:

	% twarc-archive.py ferguson /mnt/tweets/ferguson

it will get the first tweet id in tweets-0001.json and use it to write another 
file which includes any new tweets since that tweet:

	/mnt/tweets/ferguson/tweets-0002.json

This functionality was initially part of twarc.py itself, but has been split out
into a separate utility.

"""

archive_file_fmt = "tweets-%04i.json"
archive_file_pat = "tweets-(\d{4}).json$"

def search_and_archive(collection, search_terms, archive_dir):
	
	if not os.path.isdir(archive_dir):
		os.mkdir(archive_dir)

	logging.info("logging search for %s to %s", search_terms, archive_dir)

	last_archive = get_last_archive(archive_dir)
	if last_archive:
		last_id = json.loads(next(open(last_archive)))['id_str']
		tweets = twarc_instance.search(search_terms, since_id=last_id)
	else:
		tweets = twarc_instance.search(search_terms)

	next_archive = get_next_archive(archive_dir)

	# we only create the file if there are new tweets to save 
	# this prevents empty archive files
	fh = None

	archive_log = []
	for tweet in tweets:
		
		# write to file on disk
		if not fh:
			fh = open(next_archive, "w")
		logging.info("archived %s", tweet["id_str"])
		fh.write(json.dumps(tweet))
		fh.write("\n")

		# write to MongoDB
		tweet['id'] = str(tweet['id']) # convert id to string
		tweet['twitore_collection'] = collection
		dbtweet = models.MongoTweet(**tweet)
		dbtweet.save()                                                        
		logging.info("tweet inserted into db, id %s" % dbtweet.id)

		# write to log
		archive_log.append({
			"id":dbtweet.id,
			"text":dbtweet['text']
		})

	if fh:
		fh.close()
	else: 
		logging.info("no new tweets found for %s", search_terms)

	# return archive_log
	return archive_log

def get_last_archive(archive_dir):
	count = 0
	for filename in os.listdir(archive_dir):
		m = re.match(archive_file_pat, filename)
		if m and int(m.group(1)) > count:
			count = int(m.group(1))
	if count != 0:
		return os.path.join(archive_dir, archive_file_fmt % count)
	else:
		return None

def get_next_archive(archive_dir):
	last_archive = get_last_archive(archive_dir)
	if last_archive:
		m = re.search(archive_file_pat, last_archive)
		count = int(m.group(1)) + 1
	else:
		count = 1
	return os.path.join(archive_dir, archive_file_fmt % count)


def retrieveCollection(collection):
	try:
		return Collection.objects.get(name=collection)        
	except DoesNotExist:
		return False


# function to deal with messages
def msgHandle(session):
	if 'msg' in session:
		msg = session['msg']
		session.pop('msg',None)
	else:
		msg = {}

	return msg


# function to set message
def setMsg(session, msg_text, msg_type):
	try:
		session['msg'] = {
			"msg_text":msg_text,
			"msg_type":msg_type
		}
		return True
	except:
		return False


# set cron job
def setCron(mycron, collection):
	logging.info("setting cron for %s" % collection.name)

	job = mycron.new(comment="twitore_%s" % collection.name, command="curl localhost:%s/%s/search/%s" % (localConfig.twitore_app_port,localConfig.twitore_app_prefix, collection.name) )
	job.minute.every(collection.minute_frequency)
	mycron.write()
	logging.debug(mycron.crons)


# set cron job
def updateCron(mycron, job, collection):
	job.minute.every(collection.minute_frequency)
	job.command = "curl localhost:%s/%s/search/%s" % (localConfig.twitore_app_port,localConfig.twitore_app_prefix, collection.name)
	mycron.write()