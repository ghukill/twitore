# betweezered app views

# generic
import json
import time

from crontab import CronTab
from flask import jsonify, render_template

# local
import localConfig
from twitore_app import app, models

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


@app.route("{prefix}/jobs".format(prefix=localConfig.twitore_app_prefix), methods=['GET', 'POST'])
def jobs():

	# get crontab for current user
	mycron = CronTab(user=True)

	# get all jobs
	jobs = mycron.crons
	localConfig.logging.debug(jobs)

	#render page
	return render_template('jobs.html',jobs=jobs)