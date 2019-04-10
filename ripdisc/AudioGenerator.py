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

import math
import struct
import shutil

class AudioGenerator():
	_WAV_HDR = struct.Struct("< L")

	def __init__(self, length_secs = 10):
		self._length_secs = length_secs
		self._srate = 44100
		self._channels = 2
		self._resolution = 16

	@property
	def samples(self):
		return math.sin(x)

	def write_wav(self, output_filename):
		# TODO: Stupid mock
		shutil.copy("/usr/share/sounds/sound-icons/pipe.wav", output_filename)

if __name__ == "__main__":
	ag = AudioGenerator()
	ag.write_wav("x.wav")
