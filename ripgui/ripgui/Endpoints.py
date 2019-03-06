import flask
import json
import sys
from ripgui.Controller import Controller
from ripgui.Application import app

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

ctrlr = Controller(config)

@app.route("/")
def index():
	return ctrlr.serve_page(flask.request, "index")

@app.route("/status")
def status():
	return flask.jsonify(ctrlr.get_status())
