#!/usr/bin/python3
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
import multiprocessing
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

	def _start_rip(self, ripid, target_dir):
		print(ripid)

	def _check_new_jobs(self):
		for (ripid, target_dir) in self._db.get_finished_rips():
			self._start_rip(ripid, target_dir)
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
