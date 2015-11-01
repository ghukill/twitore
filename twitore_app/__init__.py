# twitore server flask app

# python
import flask

# db related
from flask import Flask, render_template, g

# crumb
import localConfig

# create app
app = flask.Flask(__name__)

# get handlers
import views
import models