#	ripmachine - GUI-driven CD/DVD ripper
#	Copyright (C) 2019-2019 Johannes Bauer
#
#	This file is part of ripmachine.
#
#	ripmachine is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	ripmachine is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with ripmachine; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

import flask
import json
import sys
from ripgui.Application import app
from ripgui.Controller import Controller

try:
	import uwsgi
except ImportError:
	uwsgi = None
if not uwsgi:
	print("WARNING: uwsgi module could not be loaded, no configuration is set.", file = sys.stderr)
	config = { }
elif "config_filename" not in uwsgi.opt:
	print("WARNING: No configuration ('config_filename') set. This might cause followup errors (e.g., KeyError).", file = sys.stderr)
	config = { }
else:
	filename = uwsgi.opt["config_filename"].decode()
	with open(filename) as f:
		config = json.load(f)

ctrlr = Controller(app, config)

@app.route("/")
def index():
	return flask.redirect(flask.url_for("static", filename = "/html/index.html"))

@app.route("/api/status")
def api_status():
	return flask.jsonify(ctrlr.ripmachine.get_status())

@app.route("/api/start/<int:drive_id>")
def api_start(drive_id):
	ctrlr.ripmachine.start(drive_id)
	return flask.jsonify({ "start": drive_id, "status": "ok" })

@app.route("/api/abort/<int:drive_id>")
def api_abort(drive_id):
	ctrlr.ripmachine.abort(drive_id)
	return flask.jsonify({ "abort": drive_id, "status": "ok" })

@app.route("/api/prepare/<int:drive_id>")
def api_prepare(drive_id):
#	ctrlr.ripmachine.abort(drive_id)
	return flask.jsonify({ "abort": drive_id, "status": "ok" })

@app.route("/api/open/<int:drive_id>")
def api_open(drive_id):
	ctrlr.ripmachine.open(drive_id)
	return flask.jsonify({ "abort": drive_id, "status": "ok" })

@app.route("/api/close/<int:drive_id>")
def api_close(drive_id):
	ctrlr.ripmachine.close(drive_id)
	return flask.jsonify({ "abort": drive_id, "status": "ok" })
