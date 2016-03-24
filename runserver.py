# -*- coding: utf-8 -*-

# betweezered twisted server wrapper
from twisted.web.wsgi import WSGIResource
from twisted.web.server import Site
from twisted.internet import reactor, defer
from twisted.internet.task import deferLater, LoopingCall
from twisted.web.server import NOT_DONE_YET
from twisted.web import server, resource
from twisted.python import log

# python modules
import json
import logging
import time
import sys

# local
import localConfig

# import crumb_http flask app
from twitore_app import app

# betweezered_app
resource = WSGIResource(reactor, reactor.getThreadPool(), app)
site = Site(resource)

# run as script
if __name__ == '__main__':

	# betweezered_app
	logging.info('''
████████╗██╗    ██╗██╗████████╗ ██████╗ ██████╗ ███████╗
╚══██╔══╝██║    ██║██║╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝
   ██║   ██║ █╗ ██║██║   ██║   ██║   ██║██████╔╝█████╗  
   ██║   ██║███╗██║██║   ██║   ██║   ██║██╔══██╗██╔══╝  
   ██║   ╚███╔███╔╝██║   ██║   ╚██████╔╝██║  ██║███████╗
''')

	# betweezered_app
	reactor.listenTCP(localConfig.twitore_app_port, site, interface="::")
	logging.info("Listening on %s" % localConfig.twitore_app_port)

	# fire reactor
	reactor.run()
