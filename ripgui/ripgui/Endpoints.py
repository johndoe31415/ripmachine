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
	return flask.redirect(flask.url_for("static", filename = "html/index.html"))

@app.route("/names")
def names():
	return flask.redirect(flask.url_for("static", filename = "html/names.html"))

@app.route("/api/status")
def api_status():
	return flask.jsonify(ctrlr.ripmachine.get_status())

@app.route("/api/start/<int:drive_id>", methods = [ "POST" ])
def api_start(drive_id):
	image = flask.request.data
	ctrlr.ripmachine.start(drive_id, image = image)
	return api_status()

@app.route("/api/retry/<int:drive_id>/<uuid:failed_ripid>")
def api_retry(drive_id, failed_ripid):
	failed_ripid = str(failed_ripid)
	ctrlr.ripmachine.retry(drive_id, failed_ripid)
	return api_status()

@app.route("/api/abort/<int:drive_id>")
def api_abort(drive_id):
	ctrlr.ripmachine.abort(drive_id)
	return api_status()

@app.route("/api/open/<int:drive_id>")
def api_open(drive_id):
	ctrlr.ripmachine.open(drive_id)
	return api_status()

@app.route("/api/close/<int:drive_id>")
def api_close(drive_id):
	ctrlr.ripmachine.close(drive_id)
	return api_status()

@app.route("/api/clear/<int:drive_id>")
def api_clear(drive_id):
	ctrlr.ripmachine.clear(drive_id)
	return api_status()

@app.route("/api/unnamed")
def api_unnamed():
	return flask.jsonify(ctrlr.ripmachine.get_unnamed())

@app.route("/api/image/<uuid:ripid>")
def api_image(ripid):
	ripid = str(ripid)
	raw_image = ctrlr.ripmachine.get_image(ripid)
	if raw_image is None:
		return flask.Response("404: Image not present\n", status = 404, headers = {
				"Content-Type":	"text/plain",
		})
	else:
		return flask.Response(raw_image,
			headers = {
				"Content-Type":	"image/jpeg",
			})

@app.route("/api/setname/<uuid:ripid>", methods = [ "POST" ])
def api_setname(ripid):
	ripid = str(ripid)
	data = flask.request.json
	ctrlr.ripmachine.set_name(ripid, data)
	return flask.jsonify({ "status": "ok" })
