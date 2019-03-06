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
import hashlib
import base64

class MediaType(enum.IntEnum):
	AudioCD = 0
	DVD = 1
	BluRay = 2
	DataCD = 3
	Unknown = 4
	NoMedium = 5

	@classmethod
	def from_str(cls, text):
		return {
			"audio":	cls.AudioCD,
			"dvd":		cls.DVD,
			"bluray":	cls.BluRay,
			"data":		cls.DataCD,
		}[text]

class CDMedium():
	_CDINFO1_REGEX = re.compile("^Disc mode is listed as: (?P<discmode>[^\n]*?)\s*\n", flags = re.MULTILINE | re.DOTALL)
	_CDINFO2_REGEX = re.compile("^Application\s*: (?P<application>[^\n]*?)\s*\n.*Volume\s*: (?P<volume>[^\n]*?)\s*\n", flags = re.MULTILINE | re.DOTALL)
	_WODIM_TRACK_INFO_REGEX = re.compile(r"^track:\s*(?P<trackno>\d+|lout)\s*lba:\s*(?P<offset>\d+)\s*\(\s*\d+\) \d{2}:\d{2}:\d{2}", flags = re.MULTILINE)

	def __init__(self, drive):
		self._drive = drive
		self._rawinfo = { }
		self._check()
		self._parse_infos()
		self._media_type = self._determine_media_type()
		self._media_id = self._determine_media_id()

	@property
	def media_type(self):
		return self._media_type

	@property
	def media_id(self):
		return self._media_id

	def _check_cdparanoia(self):
		try:
			if self._drive.verbose:
				print("Trying to determine audio TOC")
			self._rawinfo["cdparanoia"] = subprocess.check_output([ "cdparanoia", "-Q", "-d", self._drive.device ], stderr = subprocess.STDOUT)
		except subprocess.CalledProcessError:
			pass

	def _check_wodim(self):
		try:
			if self._drive.verbose:
				print("Trying to determine wodim CD info")
			self._rawinfo["wodim"] = subprocess.check_output([ "wodim", "dev=%s" % (self._drive.device), "-toc" ], stderr = subprocess.STDOUT)
		except subprocess.CalledProcessError:
			pass

	def _check_isoinfo(self):
		try:
			if self._drive.verbose:
				print("Trying to determine ISO info")
			self._rawinfo["isoinfo"] = subprocess.check_output([ "isoinfo", "-d", "-i", self._drive.device ], stderr = subprocess.STDOUT)
		except subprocess.CalledProcessError:
			pass

	def _check_cd_info(self):
		try:
			if self._drive.verbose:
				print("Trying to determine CD info")
			self._rawinfo["cdinfo"] = subprocess.check_output([ "cd-info", "-C", "--no-tracks", "--dvd", "--no-vcd", "--no-device-info", "--no-cddb", self._drive.device ], stderr = subprocess.STDOUT)
		except subprocess.CalledProcessError:
			pass

	def _compute_cddb_id(self, tracks):
		def _digitsum(x):
			result = 0
			while x > 0:
				result += x % 10
				x //= 10
			return result

		n = 0
		for track in tracks["content"]:
			total_secs = (track["offset"] + 150) // 75
			n += _digitsum(total_secs)
		t = (tracks["lout"]["offset"] - tracks["content"][0]["offset"]) // 75
		value = ((n % 0xff) << 24) | (t << 8) | len(tracks["content"])
		return "%08x" % (value)

	def _compute_musicbrainz_ids(self, tracks):
		mb_data = "%02X%02X%08X" % (tracks["content"][0]["trackno"], tracks["content"][-1]["trackno"], 150 + tracks["lout"]["offset"])
		for track in tracks["content"]:
			mb_data += "%08X" % (150 + track["offset"])
		if len(tracks["content"]) < 99:
			mb_data += "00000000" * (99 - len(tracks["content"]))
		mb_hash = hashlib.sha1(mb_data.encode("ascii")).digest()
		encoded = base64.b64encode(mb_hash).decode("ascii")
		encoded = encoded.replace("+", ".")
		encoded = encoded.replace("/", "_")
		encoded = encoded.replace("=", "-")
		return encoded

	def _parse_infos(self):
		self._rawinfo = { key: value.decode("utf-8") for (key, value) in self._rawinfo.items() }

		if "cdinfo" in self._rawinfo:
			match = self._CDINFO1_REGEX.search(self._rawinfo["cdinfo"])
			if match:
				self._rawinfo["cdinfo-discmode"] = match.groupdict()

			match = self._CDINFO2_REGEX.search(self._rawinfo["cdinfo"])
			if match:
				self._rawinfo["cdinfo-app-vol"] = match.groupdict()

		if "wodim" in self._rawinfo:
			tracks = {
				"content": [ ],
			}
			for track in self._WODIM_TRACK_INFO_REGEX.finditer(self._rawinfo["wodim"]):
				track = track.groupdict()
				track_info = { "offset": int(track["offset"]) }
				if track["trackno"] == "lout":
					tracks["lout"] = track_info
				else:
					trackno = int(track["trackno"])
					track_info["trackno"] = trackno
					tracks["content"].append(track_info)


			# Inject test data: 49HHV7Eb8UKF3aQiNmu1GR8vKTY- / 3404f606
			__tracks = {
				"content": [
					{ "trackno": 1,	"offset": 0, },
					{ "trackno": 2,	"offset": 15213 },
					{ "trackno": 3,	"offset": 32164 },
					{ "trackno": 4,	"offset": 46442 },
					{ "trackno": 5,	"offset": 63264 },
					{ "trackno": 6,	"offset": 80339 },
				],
				"lout": { "offset": 95312 }
			}

			# Compute length
			for (track, next_track) in zip(tracks["content"], tracks["content"][1:]):
				track["length"] = next_track["offset"] - track["offset"]

			if (len(tracks["content"]) >= 1) and ("lout" in tracks):
				tracks["content"][-1]["length"] = tracks["lout"]["offset"] - tracks["content"][-1]["offset"]

			# Convenience calculations on the track data
			for track in tracks["content"]:
				if "length" in track:
					track["length_bytes"] = track["length"] * 2352
					track["length_seconds"] = track["length"] / 75

			self._rawinfo["tracks"] = tracks
			self._rawinfo["id-musicbrainz"] = self._compute_musicbrainz_ids(tracks)
			self._rawinfo["id-cddb"] = self._compute_cddb_id(tracks)

	def _check(self):
		if self._drive.can_handle_media_type([ MediaType.AudioCD ]):
			self._check_cdparanoia()
			self._check_wodim()

		if self._drive.can_handle_media_type([ MediaType.DataCD, MediaType.DVD, MediaType.BluRay ]):
			self._check_isoinfo()
			self._check_cd_info()

	def _determine_media_type(self):
		media_type = MediaType.Unknown
		if "cdparanoia" in self._rawinfo:
			media_type = MediaType.AudioCD
		elif "cdinfo-discmode" in self._rawinfo:
			if self._rawinfo["cdinfo-discmode"]["discmode"] == "CD-DATA (Mode 1)":
				media_type = MediaType.DataCD
			elif self._rawinfo["cdinfo-discmode"]["discmode"] == "DVD-R":
				media_type = MediaType.DVD
		return media_type

	def _determine_media_id(self):
		media_id = { "text": "Media ID not available for medium of type '%s'." % (self.media_type.name) }
		if self.media_type in [ MediaType.DVD, MediaType.DataCD ]:
			media_id = { }
			if "cdinfo-app-vol" in self._rawinfo:
				media_id.update({
					"application":	self._rawinfo["cdinfo-app-vol"]["application"],
					"volume":		self._rawinfo["cdinfo-app-vol"]["volume"],
				})
			if "cdinfo-discmode" in self._rawinfo:
				media_id.update({
					"disc_mode":	self._rawinfo["cdinfo-discmode"]["discmode"],
				})
		elif self.media_type == MediaType.AudioCD:
			media_id = {
				"tracks":		self._rawinfo["tracks"],
				"ids": {
					"musicbrainz":	self._rawinfo["id-musicbrainz"],
					"cddb":			self._rawinfo["id-cddb"],
				},
			}
		return media_id

class CDDrive():
	_DEV_REGEX = re.compile("^Vendor\s*:\s*(?P<vendor>[^\n]*?)\s*\n.*Model\s*:\s*(?P<model>[^\n]*?)\s*\nRevision\s*:\s*(?P<revision>[^\n]*?)\s*\n", flags = re.MULTILINE | re.DOTALL)

	def __init__(self, device, restrict_media_types = None, verbose = False):
		self._device = device
		self._drive_id = None
		self._media_type = None
		self._media_id = None
		self._restrict_media_types = restrict_media_types
		self._verbose = verbose

	@property
	def verbose(self):
		return self._verbose

	def can_handle_media_type(self, media_types):
		return (self._restrict_media_types is None) or any(media_type in self._restrict_media_types for media_type in media_types)

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
		if self._verbose:
			print("Checking drive ID of %s" % (self._device))
		stdout = subprocess.check_output([ "cd-drive", "-i", self._device ], stderr = subprocess.DEVNULL)
		stdout = stdout.decode("utf-8")
		result = self._DEV_REGEX.search(stdout)
		if result is None:
			raise Exception("Couldn't get device ID for device '%s'" % (self._device))
		self._drive_id = result.groupdict()
		return self._drive_id


	def check_media_id(self):
		if self._verbose:
			print("Checking media ID of %s" % (self._device))
		medium = CDMedium(self)
		self._media_type = medium.media_type
		self._media_id = medium.media_id
		if self._media_type == MediaType.Unknown:
			print("Unknown disc mode: %s" % (medium.info))

	def __str__(self):
		return "Drive<%s: %s with %s (%s)>" % (self.device, str(self.drive_id), self.media_type.name, str(self.media_id))
