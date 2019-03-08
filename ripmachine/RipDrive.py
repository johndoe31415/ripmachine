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

import os
import json
import subprocess
from .RipEnums import RipStatus

class RipDrive():
	def __init__(self, config, drive_config):
		self._config = config
		self._name = drive_config["name"]
		self._dev = self._config.get_file(drive_config["dev"])
		self._status = RipStatus.Idle
		self._proc = None
		self._rip_target = None
		self._last_result = None

	@property
	def name(self):
		return self._name

	@property
	def status(self):
		return self._status

	def abort(self):
		if self._proc is not None:
			self._proc.kill()
		self._proc = None
		self._status = RipStatus.Aborted

	def start(self, output_directory, rip_id):
		if self._proc is not None:
			raise Exception("Ripping already in progress.")
		self._rip_target = output_directory
		self._status = RipStatus.Running
		ripdisc_binary = self._config.get_binary("ripdisc")
		cmd = [ ripdisc_binary, "-f", "-m", "audio", "--callback-id", rip_id, self._dev, output_directory ]
		self._proc = subprocess.Popen(cmd)

	def _check_process(self):
		if self._proc is None:
			return
		try:
			result = self._proc.wait(timeout = 0)
			self._proc = None
			self._status = RipStatus.Idle
		except subprocess.TimeoutExpired:
			pass

	def _read_status_json(self):
		if self._rip_target is None:
			return None
		self._check_process()
		try:
			with open(self._rip_target + "/state.json") as f:
				status = json.load(f)
				return status
		except (FileNotFoundError, json.JSONDecodeError):
			return None

	def get_status(self):
		result = {
			"name":					self.name,
			"status":				self.status.name.lower(),
			"device":				self._dev,
			"progress":				0,
			"data":					0,
			"speed":				0,
		}
		status = self._read_status_json()
		if status is not None:
			result["progress"] = status["progress"]["bytes_read"]
			result["data"] = status["progress"]["disc_size"]
			result["speed"] = status["progress"]["speed"]
		return result
