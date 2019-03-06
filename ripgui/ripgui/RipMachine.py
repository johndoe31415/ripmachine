import os
import enum
import contextlib

class RipStatus(enum.IntEnum):
	Idle = 0
	Ripping = 1

class RipDrive():
	def __init__(self, drive_config):
		self._name = drive_config["name"]
		self._orig_dev = drive_config["dev"]
		self._dev = os.path.realpath(self._orig_dev)
		self._status = RipStatus.Idle

	@property
	def name(self):
		return self._name

	@property
	def status(self):
		return self._status

	def get_status(self):
		return {
			"name":					self.name,
			"status":				self.status.name.lower(),
			"progress":				0,
			"data":					123 * 1024 * 1024,
			"original_device":		self._orig_dev,
			"device":				self._dev,
		}

class RipMachine():
	def __init__(self, config):
		self._work_dir = self._get_dir(config["directories"]["work"])
		self._output_dir = self._get_dir(config["directories"]["work"])
		self._drives = [ RipDrive(drive_data) for drive_data in config["drives"] ]

	@property
	def drives(self):
		return iter(self._drives)

	def get_status(self):
		return {
			"drives": [ drive.get_status() for drive in self.drives ],
		}

	@staticmethod
	def _get_dir(dirname):
		dirname = os.path.realpath(os.path.expanduser(dirname))
		with contextlib.suppress(FileExistsError):
			os.makedirs(dirname)
		return dirname
