# betweezered app views

# generic
import json
import time

from crontab import CronTab
from flask import jsonify, render_template, request
from mongoengine import DoesNotExist

# local
import localConfig
from localConfig import logging
from twitore_app import app, models
import utils




@app.route("{prefix}/jobs".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def jobs():

	# get crontab for current user
	mycron = CronTab(user=True)

	# get all jobs
	jobs = mycron.crons
	localConfig.logging.debug(jobs)

	#render page
	return render_template('jobs.html',jobs=jobs)




# route for performing search, HTTP trigger for work
@app.route("{prefix}/search/<collection>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def search(collection):

	logging.info("Performing search for %s" % collection)
	
	# retrieve collection mongo record
	try:
		c = models.Collection.objects.get(name=collection)
		logging.info("Retrieved %s %s" % (c.name,c.id))
	except DoesNotExist:
		logging.info("collection does not exist")
		return jsonify({"status":False})


	# run search (where collection name is used for )
	archive_dir = "/".join([localConfig.archive_directory,c.name])
	search_terms = ",".join(c.search_terms)
	logging.debug("Passing %s %s" % (search_terms,archive_dir))
	archive_log = utils.search_and_archive(collection, search_terms, archive_dir)
	logging.debug(archive_log)

	return jsonify({"archive_log":archive_log})


# route for performing search, HTTP trigger for work
@app.route("{prefix}/create_collection".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def create_collection():

	if request.method =="GET":
		return render_template("create_collection.html")

	if request.method == "POST":
		logging.debug(request.form)

		# create collection
		'''
		Need error checking here, if collection already exists, prevent from creating another
		'''

		# check for collection name



		c = models.Collection()
		c.name = request.form['name']
		c.search_terms = request.form['search_terms'].split(",")
		c.save()
		logging.debug("created collection %s" % c.id)

		return str(c.id)


# route for performing search, HTTP trigger for work
@app.route("{prefix}/delete_collection/<collection>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def delete_collection(collection):

	# retrieve collection mongo record
	logging.debug("attempting to delete %s" % collection)
	try:
		c = models.Collection.objects.get(name=collection)        
	except DoesNotExist:
		logging.debug("could not find collection to delete")
		return jsonify({'status':False})

	# delete collection
	models.Collection.delete(c)
	'''
	Consider removing archived tweets from filesystem?
	'''
	return jsonify({'status':True})

















# # return json for tweet
# @app.route("{prefix}/tweets/<limit>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
# def tweet(limit):

# 	renderdict = {}

# 	# return tweet json
# 	renderdict['tweets'] = models.MongoTweet.objects().limit(int(limit))
# 	renderdict['count'] = models.MongoTweet.objects.count()
# 	renderdict['limit'] = limit

# 	# add search terms
# 	renderdict['search_terms'] = localConfig.search_terms

# 	return render_template('tweets.htm',renderdict=renderdict)