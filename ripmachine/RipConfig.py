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

import json
import os
import contextlib

class RipConfig():
	def __init__(self, filename):
		self._config_dir = os.path.realpath(os.path.dirname(filename))
		with open(filename) as f:
			self._config = json.load(f)

	def _substitute(self, text):
		text = text.replace("${configdir}", self._config_dir)
		return text

	@property
	def drives(self):
		return iter(self._config["drives"])

	def get_binary(self, name):
		return self.get_file(self._config["binaries"][name])

	def get_directory_by_name(self, name):
		return self.get_directory(self._config["directories"][name])

	def get_file(self, filename):
		filename = os.path.realpath(os.path.expanduser(self._substitute(filename)))
		return filename

	def get_directory(self, path):
		directory = self.get_file(path)
		with contextlib.suppress(FileExistsError):
			os.makedirs(directory)
		return directory

	@property
	def fast_rip(self):
		return self._config.get("options", { }).get("fast_rip", False)

	@property
	def mock_mode(self):
		return self._config.get("options", { }).get("mock", False)
