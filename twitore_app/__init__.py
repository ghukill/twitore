# twitore server flask app

# localConfig
import localConfig

# python
import flask
from flask import Flask, render_template, g

# twarc
from twarc import Twarc
# global twarc instance
twarc_instance = Twarc(localConfig.client_key, localConfig.client_secret, localConfig.access_token, localConfig.access_token_secret)

# crontab
from crontab import CronTab
mycron = CronTab(user=True)

# create app
app = flask.Flask(__name__)

# set session key
app.secret_key = 'twitore_is_the_bomb'

# Flask/MongoEngine
from flask.ext.mongoengine import MongoEngine
app.config['MONGODB_SETTINGS'] = {
    'db': 'twitore_dev'
}
db = MongoEngine(app)

# setup cache
from flask.ext.cache import Cache
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

# get handlers (should be last)
import views
import models