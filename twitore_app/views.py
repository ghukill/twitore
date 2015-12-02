# betweezered app views

# generic
import json
import time

from crontab import CronTab
from flask import jsonify, render_template, request, redirect, url_for, session
from mongoengine import DoesNotExist

# local
import localConfig
from localConfig import logging
from twitore_app import app, models, mycron
import utils




# HTML VIEWS --------------------------------------------------------------------------------- #

# index
@app.route("/{prefix}".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def index():

	return render_template('index.html')


# collections view
@app.route("/{prefix}/collections".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def collections():

	# deal with message
	msg = utils.msgHandle(session)

	data = []
	collections = models.Collection.objects()

	'''
	This needs to be paginated
	'''
	for collection in collections:
		s = models.MongoTweet.objects().filter(twitore_collection=collection.name)
		data.append({
			"count":s.count(),
			"name":collection.name,
			'minute_frequency':collection.minute_frequency			
		})

	logging.debug(mycron.user)
	logging.debug(mycron.crons)

	return render_template('collections.html', data=data, msg=msg)


# single collection view
@app.route("/{prefix}/collection/<name>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def collection(name):

	# deal with message
	msg = utils.msgHandle(session)

	data = {}

	c = models.Collection.objects.get(name=name)
	data['collection'] = c

	# stringify search terms
	data['collection']['search_terms'] = ", ".join(data['collection']['search_terms'])

	# get job cron
	try:
		job = mycron.find_comment('twitore_{name}'.format(name=name)).next()
		logging.debug(job.command)
	except:
		logging.warning('could not find cron')

	return render_template('collection.html', data=data, msg=msg)	


# route for creating collection
@app.route("/{prefix}/create_collection".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
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
		utils.setCron(mycron,c)

		# set msg in session		
		utils.setMsg(session,"collection created","msg_success")

		return redirect("/{prefix}/collections".format(prefix=localConfig.twitore_app_prefix))


# route for updating collection
@app.route("/{prefix}/update_collection/<name>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
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
	job = mycron.find_comment('twitore_{name}'.format(name=name))
	job = list(job)
	logging.debug(job)

	# update cron
	'''
	Consider improving the logic here
	'''
	if len(job) > 0:
		if c.minute_frequency == 0:
			utils.deleteCron(mycron, job[0], c)
		elif c.minute_frequency >= 1 and c.minute_frequency <= 59:
			utils.updateCron(mycron,job[0],c)
		else:
			logging.warning('frequency must be between 1-59 minutes. aborting.')
			utils.setMsg(session,"collection could not be updated. frequency must be between 1-59 minutes. aborted.","msg_alert")
			return redirect("/{prefix}/collection/{name}".format(prefix=localConfig.twitore_app_prefix,name=name))
	
	# set cron if not there
	else:
		# set cron job
		utils.setCron(mycron,c)

	# set msg in session		
	utils.setMsg(session,"collection updated","msg_success")

	return redirect("/{prefix}/collection/{name}".format(prefix=localConfig.twitore_app_prefix,name=name))
	

# route for deleting collection
@app.route("/{prefix}/delete_collection/<name>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def delete_collection(name):

	# retrieve collection mongo record
	logging.debug("attempting to delete %s" % name)
	try:
		c = models.Collection.objects.get(name=name)        
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
	job = list(mycron.find_comment('twitore_%s' % name))
	logging.debug(job)
	if len(job) == 1:
		utils.deleteCron(mycron, job[0], c)		
	else:
		logging.debug('could not find cron to delete')

	# set msg in session		
	utils.setMsg(session,"collection deleted","msg_success")

	# if all goes well...	
	return redirect("/{prefix}/collections".format(prefix=localConfig.twitore_app_prefix))


# # route for all tweets paginated
# @app.route("/{prefix}/all_tweets/<int:page>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
# def all_tweets(page=1):

# 	pt = models.MongoTweet.objects.paginate(page=page, per_page=10)

# 	return render_template("tweets.html",pt=pt)


# single collection view
@app.route("/{prefix}/collection/<name>/tweets/<int:page>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def collection_tweets(name,page=1):

	c = models.Collection.objects.get(name=name)

	data = {
		"collection":c
	}

	pt = models.MongoTweet.objects.filter(twitore_collection=name).order_by('-id').paginate(page=page, per_page=25)

	for tweet in pt.items:
		logging.debug("tweet id: %s" % tweet.id)

	return render_template('tweets.html', data=data, pt=pt)	




# API ROUTES --------------------------------------------------------------------------------- #

# route for performing search, HTTP trigger for work
@app.route("/{prefix}/search/<collection>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
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
	# search_terms = ",".join(c.search_terms)
	logging.debug("Passing %s %s" % (c.search_terms,archive_dir))
	archive_log = utils.search_and_archive(collection, c.search_terms, archive_dir)


	return jsonify({"archive_log":archive_log})























# # return json for tweet
# @app.route("/{prefix}/tweets/<limit>".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
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
# @app.route("/{prefix}/jobs".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
# def jobs():

# 	# get crontab for current user
# 	mycron = CronTab(user=True)

# 	# get all jobs
# 	jobs = mycron.crons
# 	localConfig.logging.debug(jobs)

# 	#render page
# 	return render_template('jobs.html',jobs=jobs)