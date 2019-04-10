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
				status varchar NOT NULL,
				imageid uuid NULL
			);
			""")
			self._conn.commit()

		# If we had processes that were running previous, we consider them dead now.
		self._cursor.execute("UPDATE rips SET end_utc = ?, status = 'rebooted' WHERE end_utc IS NULL;", (self._now(), ))
		self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE ripimages (
				imageid uuid PRIMARY KEY,
				image blob NOT NULL
			);
			""")
			self._conn.commit()

		with contextlib.suppress(sqlite3.OperationalError):
			self._cursor.execute("""
			CREATE TABLE ripmeta (
				ripid uuid PRIMARY KEY,
				artist varchar NULL,
				album varchar NULL
			);
			""")
			self._conn.commit()
		self._lock = threading.Lock()

	def _now(self):
		return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

	def __create_image(self, image):
		imageid = str(uuid.uuid4())
		self._cursor.execute("INSERT INTO ripimages (imageid, image) VALUES (?, ?);", (imageid, image))
		return imageid

	def __create(self, output_dir, imageid = None):
		ripid = str(uuid.uuid4())
		now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
		self._cursor.execute("INSERT INTO rips (ripid, start_utc, target_directory, status, imageid) VALUES (?, ?, ?, 'running', ?);", (ripid, now, output_dir, imageid))
		self._conn.commit()
		return ripid

	def create(self, output_dir, image = None):
		with self._lock:
			if image is not None:
				imageid = self.__create_image(image)
			else:
				imageid = None
			return self.__create(output_dir, imageid)

	def finish(self, ripid, status):
		with self._lock:
			self._cursor.execute("UPDATE rips SET end_utc = ?, status = ? WHERE ripid = ?", (self._now(), status, ripid))
			self._conn.commit()

	def retry(self, output_dir, failed_ripid):
		with self._lock:
			row = self._cursor.execute("SELECT status, imageid FROM rips WHERE ripid = ?;", (failed_ripid, )).fetchone()
			if row is None:
				raise Exception("No such rip id")
				return None
			(status, imageid) = row
			if status not in [ "aborted", "errored" ]:
				# Resume not permitted
				raise Exception("Resume not permitted, rip status was '%s'" % (status))

			new_ripid = self.__create(output_dir, imageid)

			# Copy metadata (if there is any)
			meta = self._cursor.execute("SELECT artist, album FROM ripmeta WHERE ripid = ?;", (failed_ripid, )).fetchone()
			if meta is not None:
				self._cursor.execute("INSERT INTO ripmeta (ripid, artist, album) VALUES (?, ?, ?);", (new_ripid, meta[0], meta[1]))
				self._conn.commit()

			return new_ripid

	def get_unnamed(self):
		with self._lock:
			return self._cursor.execute("""SELECT rips.ripid, rips.imageid, start_utc, status FROM rips
					LEFT JOIN ripmeta ON rips.ripid = ripmeta.ripid
					WHERE ((status = 'running') OR (status = 'completed')) AND (ripmeta.ripid IS NULL)
					ORDER BY start_utc ASC
			""").fetchall()

	def get_image(self, imageid):
		with self._lock:
			row = self._cursor.execute("SELECT image FROM ripimages WHERE imageid = ?;", (imageid, )).fetchone()
			if row is not None:
				return row[0]
			else:
				return None

	def set_name(self, ripid, values):
		with self._lock:
			(count, ) = self._cursor.execute("SELECT COUNT(*) FROM ripmeta WHERE ripid = ?;", (ripid, )).fetchone()
			if count == 0:
				self._cursor.execute("INSERT INTO ripmeta (ripid, artist, album) VALUES (?, ?, ?);", (ripid, values.get("artist", ""), values.get("album", "")))
			else:
				self._cursor.execute("UPDATE ripmeta SET artist = ?, album = ? WHERE ripid = ?;", (values.get("artist", ""), values.get("album", ""), ripid))
			self._conn.commit()

	def get_finished_rips(self):
		with self._lock:
			rows = self._cursor.execute("""
				SELECT rips.ripid, target_directory, artist, album FROM rips
					LEFT JOIN ripmeta ON rips.ripid = ripmeta.ripid
					WHERE (status = 'completed') AND (ripmeta.ripid IS NOT NULL);
				""").fetchall()
			return rows

	def mark_converted(self, ripid):
		with self._lock:
			self._cursor.execute("UPDATE rips SET status = 'converted' WHERE (ripid = ?) AND (status = 'completed');", (ripid, ))
			self._conn.commit()
