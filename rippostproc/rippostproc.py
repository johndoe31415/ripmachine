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

import sys
import multiprocessing
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
parser.add_argument("config", metavar = "config_file", type = str, help = "Ripmachine configuration file to use")
args = parser.parse_args(sys.argv[1:])

print(args)
joifds

ripconfig = RipConfig(args.config)
print(ripconfig)

jobserver = JobServer(1)
handles = jobserver.runall([
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
	[ "sleep", "1" ],
])
for handle in handles:
	handle.wait()
print("done")
jobserver.wait()
