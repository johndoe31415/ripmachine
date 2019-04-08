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
import signal
import base64
import time
from CDDrive import CDDrive, MediaType
from Tools import FileTools
from SpeedAverager import SpeedAverager
from SpeedMonitor import SpeedMonitor
from DeathSig import set_pdeathsig

class RipCore():
	def __init__(self, args):
		self._args = args
		restrict_media_types = set([ MediaType.from_str(media_type) for media_type in self._args.force_medium ])
		if len(restrict_media_types) == 0:
			restrict_media_types = None
		if self._args.mock is None:
			self._drive = CDDrive(self._args.drive, restrict_media_types = restrict_media_types, verbose = self._args.verbose)
		else:
			dirname = os.path.dirname(__file__)
			with open(dirname + "/mock_" + self._args.mock + ".json") as f:
				mock_data = json.load(f)
			def decode(value):
				if isinstance(value, dict) and (value.get("type") == "bytes"):
					return base64.b64decode(value["value"])
				else:
					return value
			mock_data = { key: decode(value) for (key, value) in mock_data.items() }
			self._drive = CDDrive(self._args.drive, mock_data = mock_data, verbose = self._args.verbose)
		self._state = "idle"
		self._error = None
		self._progress = None
		self._speed_monitor = SpeedMonitor()
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
			"graph": self._speed_monitor.data,
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
			if self._args.verbose >= 1:
				print(" ".join(command))
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
			if self._args.verbose >= 2:
				output = None
			else:
				output = subprocess.DEVNULL
			proc = subprocess.Popen(command, stdout = output, stderr = output, preexec_fn = lambda: set_pdeathsig(signal.SIGKILL))
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
					self._speed_monitor.record(pos)
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
		subprocess.check_call(unlock_cmd, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL, preexec_fn = lambda: set_pdeathsig(signal.SIGKILL))

		return self._rip_data_cd(destination_dir, image_filename = "dvd.iso")

	def _rip_audio_track(self, track_no, destination_dir):
		if track_no is not None:
			output_filename = "%s/audio_%02d.wav" % (destination_dir, track_no)
		else:
			# Rip whole CD
			if self._args.audiorip == "cdparanoia":
				raise NotImplementedError(self._args.audiorip)
			elif self._args.audiorip == "cdda2wav":
				output_filename = "%s/audio" % (destination_dir)
			else:
				raise NotImplementedError(self._args.audiorip)

		if self._args.audiorip == "cdparanoia":
			log_summary_file = "%s/summary_%02d.txt" % (destination_dir, track_no)
			log_debug_file = "%s/debug_%02d.txt" % (destination_dir, track_no)
			cmd = [ "cdparanoia" ]
			cmd += [ "--force-cdrom-device=%s" % (self._drive.device) ]
			cmd += [ "--log-summary=%s" % (log_summary_file) ]
			cmd += [ "--log-debug=%s" % (log_debug_file) ]
			if self._args.fast_rip:
				cmd += [ "--disable-paranoia", "--disable-extra-paranoia" ]
#			cmd += [ "--force-read-speed", "2" ]
#			cmd += [ "--force-read-speed", "1" ]
#			cmd += [ "--force-read-speed", "1", "-Y" ]
#			cmd += [ "--force-read-speed", "1", "-Y", "-Z" ]
			cmd += [ str(track_no), output_filename ]
		elif self._args.audiorip == "cdda2wav":
			cmd = [ "cdda2wav" ]
			cmd += [ "-D", self._drive.device ]
			cmd += [ "-l", "128" ]
			if not self._args.fast_rip:
				cmd += [ "-paranoia" ]
			if track_no is not None:
				cmd += [ "track=%d" % (track_no) ]
			else:
				# Batch mode, rip whole CD
				cmd += [ "-B" ]
			cmd += [ output_filename ]
		else:
			raise NotImplementedError(self._args.audiorip)
		return cmd

	def _rip_audio_cd(self, destination_dir):
		self._state = "ripping"
		track_count = len(self._drive.media_id["tracks"]["content"])
		commands = [ ]
		disc_size = 0
		for (track_no, track) in enumerate(self._drive.media_id["tracks"]["content"], 1):
			disc_size += track["length_bytes"]
		commands.append(self._rip_audio_track(None, destination_dir))

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

		self._execute_cmds(commands, progress = _determine_progress, disc_size = disc_size)

	def _mock_rip(self):
		self._state = "ripping"

		class ProgressMock():
			def __init__(self, total_size, time_secs):
				self._total_size = total_size
				self._t0 = time.time()
				self._time_secs = time_secs

			@property
			def total_size(self):
				return self._total_size

			@property
			def time_secs(self):
				return self._time_secs

			def progress(self):
				now = time.time()
				tdiff = now - self._t0
				amount_per_sec = self._total_size / self._time_secs
				pos = round(tdiff * amount_per_sec)
				if pos > self._total_size:
					pos = self._total_size
				return pos

		prog_mock = ProgressMock(time_secs = 35, total_size = 123 * 1024 * 1024)
		cmds = [
			[ "sleep", str(prog_mock.time_secs) ],
		]
		self._execute_cmds(cmds, prog_mock.progress, prog_mock.total_size)

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
		if self._args.mock is not None:
			self._mock_rip()
		else:
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
