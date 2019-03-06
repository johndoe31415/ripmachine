#	knitpi - Raspberry Pi interface for Brother KH-930 knitting machine
#	Copyright (C) 2018-2018 Johannes Bauer
#
#	This file is part of knitpi.
#
#	knitpi is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	knitpi is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with knitpi; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import time
import random
import json
import flask
import threading
import mako.lookup
import subprocess
import gevent.event
from .RipMachine import RipMachine

class Controller(object):
	def __init__(self, config):
		self._config = config
		self._template_lookup = mako.lookup.TemplateLookup([ self._config["directories"]["templates"] ], input_encoding = "utf-8", strict_undefined = True)
		self._ripmachine = RipMachine(self._config)

	def serve_page(self, request, template_name, args = None):
		if args is None:
			args = {
				"debugging":		self._config.get("debugging", False),
			}
		try:
			template = self._template_lookup.get_template(template_name + ".html")
		except mako.exceptions.TopLevelLookupException:
			return flask.Response("Template '%s' not found.\n" % (template_name), status = 404, mimetype = "text/plain")
		additional_data_handler = getattr(self, "_handler_" + template_name, None)
		if additional_data_handler is not None:
			additional_data_handler(args)
		result = template.render(**args)
		return result

	def get_status(self):
		return self._ripmachine.get_status()
