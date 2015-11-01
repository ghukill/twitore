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

# get handlers
import views
import models