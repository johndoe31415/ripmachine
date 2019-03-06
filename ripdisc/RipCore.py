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
import shutil
import datetime
import subprocess
from CDDrive import CDDrive, MediaType
from Tools import FileTools
from SpeedAverager import SpeedAverager

class RipCore():
	def __init__(self, args):
		self._args = args
		restrict_media_types = set([ MediaType.from_str(media_type) for media_type in self._args.force_medium ])
		if len(restrict_media_types) == 0:
			restrict_media_types = None
		self._drive = CDDrive(self._args.drive, restrict_media_types = restrict_media_types, verbose = self._args.verbose)
		self._state = "idle"
		self._error = None
		self._progress = None
		self._start_utc = datetime.datetime.utcnow()

	def write_status(self):
		now = datetime.datetime.utcnow()
		status = {
			"drive": self._drive.drive_id,
			"callback_id": self._args.callback_id,
			"medium": {
				"type":		self._drive.media_type.name,
				"info":		self._drive.media_id,
			},
			"state": self._state,
			"error": self._error,
			"progress": self._progress,
			"runtime": {
				"start": {
					"ts_utc":	self._start_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
					"unix":		self._start_utc.timestamp(),
				},
				"now": {
					"ts_utc":	now.strftime("%Y-%m-%dT%H:%M:%SZ"),
					"unix":		now.timestamp(),
				},
			},
		}
		with open(self._args.destdir + "/state.json", "w") as f:
			json.dump(status, f, sort_keys = True, indent = 4)
			f.write("\n")

	def _execute_cmds(self, commands, progress, disc_size):
		speed = SpeedAverager()
		for (cid, command) in enumerate(commands, 1):
			pos = progress()
			speed.add(pos)
			self._progress = {
				"command":	command,
				"number": cid,
				"total": len(commands),
				"bytes_read": pos,
				"disc_size": disc_size,
				"speed": speed.real_speed,
			}
			self.write_status()
			proc = subprocess.Popen(command, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
			while True:
				try:
					result = proc.wait(self._args.update_delay)
					if result == 0:
						break
					else:
						raise Exception("Process failed with return code %d." % (result))
				except subprocess.TimeoutExpired:
					pos = progress()
					speed.add(pos)
					self._progress["bytes_read"] = pos
					self._progress["speed"] = speed.real_speed
					self.write_status()
		self._progress["bytes_read"] = progress()
		self.write_status()

	def _rip_data_cd(self, destination_dir, image_filename = "image.iso"):
		self._state = "ripping"
		outfile = destination_dir + "/" + image_filename
		ddrescue_log = destination_dir + "/ddrescue.log"
		commands = [
			[ "ddrescue", "-n", "-a", "100000", "-b", "2048", "-c", "512", self._drive.device, outfile, ddrescue_log ],
			[ "ddrescue", "-d", "-a", "100000", "-b", "2048", "-c", "512", self._drive.device, outfile, ddrescue_log ],
		]
		def _determine_progress():
			try:
				return FileTools.get_filesize(outfile)
			except FileNotFoundError:
				return 0

		disc_size = FileTools.get_filesize(self._drive.device)
		self._execute_cmds(commands, progress = _determine_progress, disc_size = disc_size)

	def _rip_dvd(self, destination_dir):
		self._state = "ripping"

		# Try to unlock DVD using mplayer before copying data
		unlock_cmd = [ "mplayer", "-vo", "none", "-ao", "none", "-dvd-device", self._drive.device, "dvd://" ]
		subprocess.check_call(unlock_cmd, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

		return self._rip_data_cd(destination_dir, image_filename = "dvd.iso")

	def _rip_audio_track(self, track_no, destination_dir):
		wav_file = "%s/audio_%02d.wav" % (destination_dir, track_no)
		log_summary_file = "%s/summary_%02d.txt" % (destination_dir, track_no)
		log_debug_file = "%s/debug_%02d.txt" % (destination_dir, track_no)
		cmd = [ "cdparanoia" ]
		cmd += [ "--force-cdrom-device=%s" % (self._drive.device) ]
		cmd += [ "--log-summary=%s" % (log_summary_file) ]
		cmd += [ "--log-debug=%s" % (log_debug_file) ]
#		if tryno <= 1:
#			pass
#		elif tryno <= 2:
#			ripcmd += [ "--force-read-speed", "2" ]
#		elif tryno <= 3:
#			ripcmd += [ "--force-read-speed", "1" ]
#		elif tryno <= 4:
#			ripcmd += [ "--force-read-speed", "1", "-Y" ]
#		else:
#			ripcmd += [ "--force-read-speed", "1", "-Y", "-Z" ]
		cmd += [ str(track_no), wav_file ]
		return cmd

	def _rip_audio_cd(self, destination_dir):
		self._state = "ripping"
		track_count = len(self._drive.media_id["tracks"]["content"])
		commands = [ ]
		disc_size = 0
		for (track_no, track) in enumerate(self._drive.media_id["tracks"]["content"], 1):
			commands.append(self._rip_audio_track(track_no, destination_dir))
			disc_size += track["length_bytes"]

		def _determine_progress():
			total_size = 0
			for (track_no, track) in enumerate(self._drive.media_id["tracks"]["content"], 1):
				wav_file = "%s/audio_%02d.wav" % (destination_dir, track_no)
				try:
					# Subtract size of WAV header
					stat = os.stat(wav_file)
					total_size += stat.st_size - 44
				except FileNotFoundError:
					pass
			if total_size < 0:
				total_size = 0
			return total_size

		disc_size = FileTools.get_filesize(self._drive.device)
		self._execute_cmds(commands, progress = _determine_progress, disc_size = disc_size)

	def commence(self):
		if os.path.exists(self._args.destdir):
			if self._args.force:
				try:
					shutil.rmtree(self._args.destdir)
				except NotADirectoryError:
					pass
				try:
					os.unlink(self._args.destdir)
				except FileNotFoundError:
					pass
			else:
				raise Exception("Destination already exists, refusing to continue: %s" % (self._args.destdir))
		os.makedirs(self._args.destdir)

		self.write_status()
		if self._drive.media_type == MediaType.DataCD:
			self._rip_data_cd(self._args.destdir)
		elif self._drive.media_type == MediaType.DVD:
			self._rip_dvd(self._args.destdir)
		elif self._drive.media_type == MediaType.AudioCD:
			self._rip_audio_cd(self._args.destdir)
		else:
			self._state = "error"
			self._error = "Do not know how to handle media type %s." % (self._drive.media_type.name)

		self._state = "done"
		self.write_status()
