# betweezered app views

# generic
import json
import time

from crontab import CronTab
from flask import jsonify, render_template, request, redirect, url_for
from mongoengine import DoesNotExist

# local
import localConfig
from localConfig import logging
from twitore_app import app, models, mycron
import utils




# HTML VIEWS --------------------------------------------------------------------------------- #

# index
@app.route("{prefix}".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def index():

	return render_template('index.html')


# collections
@app.route("{prefix}/collections".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def collections():

	msg={}

	data = []
	collections = models.Collection.objects()

	for collection in collections:		
		s = models.MongoTweet.objects().filter(twitore_collection=collection.name)
		data.append({
			"count":s.count(),
			"name":collection.name			
		})

	return render_template('collections.html', data=data, msg=msg)


# collection
@app.route("{prefix}/collection/<name>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def collection(name):

	msg = {}
	data = {}

	c = models.Collection.objects.get(name=name)
	data['collection'] = c

	# stringify search terms
	data['collection']['search_terms'] = ", ".join(data['collection']['search_terms'])

	return render_template('collection.html', data=data, msg=msg)	


# route for creating collection
@app.route("{prefix}/create_collection".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def create_collection():

	data = {}

	if request.method =="GET":
		return render_template("create_collection.html")

	if request.method == "POST":
		logging.debug(request.form)

		# create collection
		collection = request.form['name']

		# check for collection name
		try:
			c = models.Collection.objects.get(name=collection)        
			return jsonify({'status':False})
		except DoesNotExist:
			logging.debug("collection does not exist, continuing")

			c = models.Collection()
			c.name = request.form['name']
			c.search_terms = [term.strip() for term in request.form['search_terms'].split(",")]
			c.minute_frequency = int(request.form['minute_frequency'])
			c.save()
			logging.debug("created collection %s" % c.id)

			# set cron job
			job = mycron.new(comment="twitore_%s" % collection, command="curl localhost:5001/twitore/search/%s" % collection)
			job.minute.every(c.minute_frequency)
			mycron.write()

			return redirect("{prefix}/collections".format(prefix=localConfig.twitore_app_prefix))
			


# route for updating collection
@app.route("{prefix}/update_collection/<name>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def update_collection(name):

	data = {}

	# assuming POST
	logging.debug(request.form)	

	# check for collection name
	try:
		c = models.Collection.objects.get(name=name)        
	except DoesNotExist:
		logging.debug("collection does not exist, continuing")
		return jsonify({'status':False})

	c.search_terms = [term.strip() for term in request.form['search_terms'].split(",")]
	c.minute_frequency = int(request.form['minute_frequency'])
	c.save()
	logging.debug("updated collection %s" % c.id)

	# update cron job
	try:
		job = mycron.find_comment('twitore_{name}'.format(name=name)).next()
		job.minute.every(c.minute_frequency)
		mycron.write()

		msg = {
			"msg_text":"Collection updated!",
			"msg_type":"msg_success"
		}
	except:
		msg = {
			"msg_text":"Collection could not be updated.",
			"msg_type":"msg_alert"
		}

	# prep for return
	# stringify search terms
	data['collection'] = c
	data['collection']['search_terms'] = ", ".join(data['collection']['search_terms'])

	# conside reworking where not directly rendering the template, but the route instead
	return render_template('collection.html', data=data, msg=msg)


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
	Consider removing archived tweets from monogodb?
	'''	

	# remove from crontab
	cron = list(mycron.find_comment('twitore_%s' % collection))
	logging.debug(cron)
	if len(cron) == 1:
		mycron.remove(cron[0])
		mycron.write()


	# if all goes well...	
	return redirect("{prefix}/collections".format(prefix=localConfig.twitore_app_prefix))


# API ROUTES --------------------------------------------------------------------------------- #

# route for performing search, HTTP trigger for work
@app.route("{prefix}/search/<collection>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def search(collection):

	'''
	Consider pushing to worker queue (celery, rq, etc.)
	'''

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


	return jsonify({"archive_log":archive_log})























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



# # cron
# @app.route("{prefix}/jobs".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
# def jobs():

# 	# get crontab for current user
# 	mycron = CronTab(user=True)

# 	# get all jobs
# 	jobs = mycron.crons
# 	localConfig.logging.debug(jobs)

# 	#render page
# 	return render_template('jobs.html',jobs=jobs)