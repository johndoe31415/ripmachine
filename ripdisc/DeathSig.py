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

import signal
import ctypes

_PR_SET_PDEATHSIG = 1
_libc = ctypes.CDLL("libc.so.6")
def set_pdeathsig(sig = signal.SIGTERM):
    return _libc.prctl(_PR_SET_PDEATHSIG, sig)

if __name__ == "__main__":
	import subprocess
	import time
	import os
	print("Parent PID: %d" % (os.getpid()))
	proc = subprocess.Popen([ "sleep", "100" ], preexec_fn = lambda: set_pdeathsig(signal.SIGTERM))
	print("Subprocess running. PID: %d" % (proc.pid))
	while True:
		time.sleep(1)
