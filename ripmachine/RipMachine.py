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
import enum
import contextlib
import uuid
import sqlite3
import datetime
import subprocess
from .RipDB import RipDB
from .RipDrive import RipDrive

class RipMachine():
	def __init__(self, config):
		self._config = config
		self._work_dir = self._config.get_directory_by_name("work")
		self._db = RipDB(self._config.ripdb_filename)
		self._drives = [ RipDrive(self._config, drive_data, self._state_change_callback) for drive_data in config.drives ]

	def _state_change_callback(self, drive, new_state):
		rip_id = drive.rip_id
		self._db.finish(rip_id, new_state.name.lower())

	def get_drive(self, drive_id):
		return self._drives[drive_id]

	def start(self, drive_id, image = None):
		output_dir = self._config.get_directory("%s/rips/%s" % (self._work_dir, datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")))
		rip_id = self._db.create(output_dir, image)
		self._drives[drive_id].start(output_dir, rip_id)

	def open(self, drive_id):
		subprocess.Popen([ "eject", self._drives[drive_id].device ])

	def close(self, drive_id):
		subprocess.Popen([ "eject", "-t", self._drives[drive_id].device ])

	def abort(self, drive_id):
		self._drives[drive_id].abort()

	def clear(self, drive_id):
		self._drives[drive_id].clear()

	def retry(self, drive_id, failed_rip_id):
		output_dir = self._config.get_directory("%s/rips/%s" % (self._work_dir, datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")))
		rip_id = self._db.retry(output_dir, failed_rip_id)
		self._drives[drive_id].start(output_dir, rip_id)

	@property
	def drives(self):
		return iter(self._drives)

	def get_status(self):
		return {
			"drives": [ drive.get_status() for drive in self.drives ],
		}

	def get_unnamed(self):
		return [
			{
				"ripid":		item[0],
				"imageid":		item[1],
				"start_utc":	item[2],
				"status":		item[3],
			} for item in self._db.get_unnamed()
		]

	def get_image(self, ripid):
		image_raw = self._db.get_image(ripid)
		return image_raw

	def set_name(self, ripid, values):
		self._db.set_name(ripid, values)

if __name__ == "__main__":
	import time
	import json
	with open("../ripgui_dev.json") as f:
		config = json.load(f)
	rm = RipMachine(config)
	drive_id = 0
	drive = list(rm.drives)[drive_id]
	rm.start(drive_id)
#	print(rm)
	while True:
		print(drive.get_status())
		time.sleep(5)
