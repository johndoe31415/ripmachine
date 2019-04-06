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

import subprocess
import threading
import multiprocessing

class CompletionHandle():
	def __init__(self):
		self._cond = threading.Condition()
		self._finished = False
		self._successful = None

	def wait(self):
		while True:
			with self._cond:
				if self._finished:
					return self._successful
				self._cond.wait()

	def complete(self, success):
		self._finished = True
		self._successful = success
		with self._cond:
			self._cond.notify_all()

class JobServer():
	def __init__(self, processes = None):
		if processes is None:
			processes = multiprocessing.cpu_count()
		self._lock = threading.Lock()
		self._process_count = processes
		self._process_sem = threading.Semaphore(self._process_count)
		self._thread_count = threading.Semaphore(1000)

	def _run_function(self, cmd, chandle):
		self._process_sem.acquire()
		try:
			subprocess.check_call(cmd)
			chandle.complete(True)
		except subprocess.CalledProcessError:
			chandle.complete(False)
		finally:
			self._process_sem.release()
			self._thread_count.release()

	def run(self, cmd):
		self._thread_count.acquire()
		chandle = CompletionHandle()
		thread = threading.Thread(target = self._run_function, args = (cmd, chandle), daemon = True)
		thread.start()
		return chandle

	def runall(self, cmds):
		return [ self.run(cmd) for cmd in cmds ]

	def wait(self):
		for i in range(self._process_count):
			self._process_sem.acquire()
