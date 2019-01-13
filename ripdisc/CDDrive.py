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

import re
import enum
import subprocess

class MediaType(enum.IntEnum):
	AudioCD = 0
	DVD = 1
	BluRay = 2
	DataCD = 3
	Unknown = 4
	NoMedium = 5

class CDDrive():
	_DEV_REGEX = re.compile("^Vendor\s*:\s*(?P<vendor>[^\n]*?)\s*\n.*Model\s*:\s*(?P<model>[^\n]*?)\s*\nRevision\s*:\s*(?P<revision>[^\n]*?)\s*\n", flags = re.MULTILINE | re.DOTALL)
	_CDINFO1_REGEX = re.compile("^Disc mode is listed as: (?P<discmode>[^\n]*?)\s*\n", flags = re.MULTILINE | re.DOTALL)
	_CDINFO2_REGEX = re.compile("^Application\s*: (?P<application>[^\n]*?)\s*\n.*Volume\s*: (?P<volume>[^\n]*?)\s*\n", flags = re.MULTILINE | re.DOTALL)

	def __init__(self, device):
		self._device = device
		self._drive_id = None
		self._media_type = None
		self._media_id = None

	@property
	def device(self):
		return self._device

	@property
	def drive_id(self):
		if self._drive_id is None:
			self.check_drive_id()
		return self._drive_id

	@property
	def media_type(self):
		if self._media_type is None:
			self.check_media_id()
		return self._media_type

	@property
	def media_id(self):
		if self._media_id is None:
			self.check_media_id()
		return self._media_id

	def check_drive_id(self):
		stdout = subprocess.check_output([ "cd-drive", "-i", self._device ], stderr = subprocess.DEVNULL)
		stdout = stdout.decode("utf-8")
		result = self._DEV_REGEX.search(stdout)
		if result is None:
			raise Exception("Couldn't get device ID for device '%s'" % (self._device))
		self._drive_id = result.groupdict()
		return self._drive_id

	def check_media_id(self):
		try:
			result_cdparanoia = subprocess.check_output([ "cdparanoia", "-Q", "-d", self._device ], stderr = subprocess.STDOUT).decode("utf-8")
		except subprocess.CalledProcessError:
			result_cdparanoia = None
		try:
			result_isoinfo = subprocess.check_output([ "isoinfo", "-d", "-i", self._device ], stderr = subprocess.STDOUT).decode("utf-8")
		except subprocess.CalledProcessError:
			result_isoinfo = None
		try:
			result_cdinfo = subprocess.check_output([ "cd-info", "-C", "--dvd", "--no-vcd", "--no-device-info", "--no-cddb", self._device ], stderr = subprocess.STDOUT).decode("utf-8")
			match_cdinfo1 = self._CDINFO1_REGEX.search(result_cdinfo)
			if match_cdinfo1 is not None:
				match_cdinfo1 = match_cdinfo1.groupdict()
			match_cdinfo2 = self._CDINFO2_REGEX.search(result_cdinfo)
			if match_cdinfo2 is not None:
				match_cdinfo2 = match_cdinfo2.groupdict()
		except subprocess.CalledProcessError:
			result_cdinfo = None
			match_cdinfo1 = None
			match_cdinfo2 = None

		if result_cdparanoia is not None:
			self._media_type = MediaType.AudioCD
		elif (result_cdparanoia is None) and (result_isoinfo is not None):
			if match_cdinfo1["discmode"] == "CD-DATA (Mode 1)":
				self._media_type = MediaType.DataCD
			elif match_cdinfo1["discmode"] == "DVD-R":
				self._media_type = MediaType.DVD
			else:
				print("Unknown disc mode: %s" % (str(match_cdinfo1)))
				self._media_type = MediaType.Unknown
		else:
			self._media_type = MediaType.Unknown

		self._media_id = { "text": "Not available for this medium." }
		if self.media_type in [ MediaType.DataCD, MediaType.DVD ]:
			if match_cdinfo2 is not None:
				self._media_id = {
					"disc_mode":	match_cdinfo1["discmode"],
					"application":	match_cdinfo2["application"],
					"volume":		match_cdinfo2["volume"],
				}

	def __str__(self):
		return "Drive<%s: %s with %s (%s)>" % (self.device, str(self.drive_id), self.media_type.name, str(self.media_id))
