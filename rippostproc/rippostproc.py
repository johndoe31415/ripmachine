#!/usr/bin/python3 -u
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

import time
import sys
import json
import threading
import multiprocessing
import shutil
from ripmachine import RipConfig, RipDB
from JobServer import JobServer
from FriendlyArgumentParser import FriendlyArgumentParser

def process_cnt(text):
	value = int(text)
	if text.startswith("+") or text.startswith("-"):
		value += multiprocessing.cpu_count()
	if value < 1:
		value = 1
	return value

parser = FriendlyArgumentParser()
parser.add_argument("-p", "--processes", metavar = "count", type = process_cnt, default = "+0", help = "Number of simultaneous processes to use for encoding. Defaults to the number of CPUs that are present. When prefixed by '+' or '-', is treated as a value that is relative to the number of CPUs on the machine.")
parser.add_argument("-v", "--verbose", action = "store_true", help = "Increase verbosity.")
parser.add_argument("config", metavar = "config_file", type = str, help = "Ripmachine configuration file to use")
args = parser.parse_args(sys.argv[1:])

class RipPostProcessor():
	def __init__(self, args):
		self._args = args

		self._config = RipConfig(args.config)
		self._jobserver = JobServer(args.processes, verbose = args.verbose)
		self._db = RipDB(self._config.ripdb_filename)
		self._active = set()

	def _start_conversion_audio(self, ripid, raw_data_dir, state, meta):
		output_suffix = [ ]
		if "artist" in meta:
			output_suffix.append(meta["artist"])
		if "album" in meta:
			output_suffix.append(meta["album"])
		if len(output_suffix) > 0:
			output_suffix = " - ".join(output_suffix)
		else:
			output_suffix = "Unnamed"

		full_outdir = self._config.get_conversion_directory(output_suffix)

		cmds = [ ]
		files = state.get("files")
		if files is None:
			# TODO: Stupid workaround to convert existing files
			files = [ "audio_%02d.wav" % (x) for x in range(1, len(state["medium"]["info"]["tracks"]["content"]) + 1) ]

		for (trackno, infilename) in enumerate(files, 1):
			full_infilename = raw_data_dir + "/" + infilename
			full_outfilename = full_outdir + "/%02d %s.flac" % (trackno, output_suffix)
			cmd = [ "flac" ]
			if "artist" in meta:
				cmd += [ "-T", "ARTIST=%s" % (meta["artist"]) ]
			if "album" in meta:
				cmd += [ "-T", "ALBUM=%s" % (meta["album"]) ]
			cmd += [ "-T", "TRACKNUMBER=%d" % (trackno) ]
			cmd += [ "-T", "TRACKTOTAL=%d" % (len(files)) ]
			cmd += [ full_infilename, "-o", full_outfilename ]
			cmds.append(cmd)

		handles = self._jobserver.runall(cmds)
		all_successful = all(handle.wait() for handle in handles)
		if not all_successful:
			print("Conversion of %s / %s failed. Not all subprocesses exited successfully." % (ripid, str(meta)))
			shutil.rmtree(full_outdir)
			return
		else:
			print("Conversion %s / %s successful." % (ripid, str(meta)))
			self._db.mark_converted(ripid)

	def _start_conversion(self, ripid, raw_data_dir, meta):
		print("Starting conversion of RIP %s raw data in %s / meta %s" % (ripid, raw_data_dir, meta))
		with open(raw_data_dir + "/state.json") as f:
			state = json.load(f)
		if state["medium"]["type"] == "AudioCD":
			threading.Thread(target = self._start_conversion_audio, args = (ripid, raw_data_dir, state, meta), daemon = True).start()
		else:
			raise NotImplementedError(state["medium"]["type"])

	def _check_new_jobs(self):
		for (ripid, target_dir, artist, album) in self._db.get_finished_rips():
			if ripid not in self._active:
				self._active.add(ripid)
				meta = {
					"artist":	artist,
					"album":	album,
				}
				self._start_conversion(ripid, target_dir, meta)
				if self._jobserver.busy:
					break

	def run(self):
		try:
			while True:
				if not self._jobserver.busy:
					self._check_new_jobs()
				time.sleep(5)
		finally:
			self._jobserver.wait()

postprocessor = RipPostProcessor(args)
postprocessor.run()

print(ripdb)
handles = jobserver.runall([
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
])


for handle in handles:
	handle.wait()
print("done")
