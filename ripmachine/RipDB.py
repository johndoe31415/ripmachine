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

import contextlib
import sqlite3
import datetime
import uuid
import threading

class RipDB():
	def __init__(self, dbfilename):
		self._conn = sqlite3.connect(dbfilename, check_same_thread = False)
		self._cursor = self._conn.cursor()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE rips (
				ripid uuid PRIMARY KEY,
				start_utc timestamp NOT NULL,
				end_utc timestamp NULL,
				target_directory varchar NOT NULL,
				status varchar NOT NULL
			);
			""")
			self._conn.commit()

		# If we had processes that were running previous, we consider them dead now.
		self._cursor.execute("UPDATE rips SET end_utc = ?, status = 'rebooted' WHERE end_utc IS NULL;", (self._now(), ))
		self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE ripimages (
				ripid uuid PRIMARY KEY,
				image blob NOT NULL
			);
			""")
			self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE ripmeta (
				ripid uuid PRIMARY KEY,
				artist varchar NULL,
				title varchar NULL
			);
			""")
			self._conn.commit()
		self._lock = threading.Lock()

	def _now(self):
		return datetime.datetime.utcnow().strftime("%Y-%m-%DT%H:%M:%SZ")

	def create(self, output_dir, image = None):
		with self._lock:
			ripid = str(uuid.uuid4())
			now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
			self._cursor.execute("INSERT INTO rips (ripid, start_utc, target_directory, status) VALUES (?, ?, ?, 'running');", (ripid, now, output_dir))
			if image is not None:
				self._cursor.execute("INSERT INTO ripimages (ripid, image) VALUES (?, ?);", (ripid, image))
			self._conn.commit()
			return ripid

	def finish(self, ripid, status):
		with self._lock:
			self._cursor.execute("UPDATE rips SET end_utc = ?, status = ? WHERE ripid = ?", (self._now(), status, ripid))
			self._conn.commit()
