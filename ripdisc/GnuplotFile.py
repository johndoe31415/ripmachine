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

import collections
import subprocess
import tempfile
import io

class GnuplotFile():
	_DataSet = collections.namedtuple("DataSet", [ "values", "color", "title", "linewidth", "drawtype", "smooth" ])
	_DefaultColors = [
		"#2980b9",
		"#c0392b",
		"#2ecc71",
		"#8e44ad",
		"#f39c12",
		"#1abc9c",
	]
	def __init__(self, width = 1920, height = 1080, title = None, xlabel = None, ylabel = None, grid = False):
		self._width = width
		self._height = height
		self._title = title
		self._xlabel = xlabel
		self._ylabel = ylabel
		self._grid = grid
		self._ytickmirror = True
		self._datasets = [ ]

	@staticmethod
	def _stringify(text):
		return "\"%s\"" % (text.replace("\"", "\\\""))

	@property
	def width(self):
		return self._width

	@width.setter
	def width(self, value):
		self._width = value

	@property
	def height(self):
		return self._height

	@height.setter
	def height(self, value):
		self._height = value

	@property
	def title(self):
		return self._title

	@title.setter
	def title(self, value):
		self._title = value

	@property
	def xlabel(self):
		return self._xlabel

	@xlabel.setter
	def xlabel(self, value):
		self._xlabel = value

	@property
	def ylabel(self):
		return self._ylabel

	@ylabel.setter
	def ylabel(self, value):
		self._ylabel = value

	@property
	def grid(self):
		return self._grid

	@grid.setter
	def grid(self, value):
		self._grid = value

	@property
	def ytickmirror(self):
		return self._ytickmirror

	@ytickmirror.setter
	def ytickmirror(self, value):
		self._ytickmirror = value

	def add_dataset(self, data, color = None, title = None, linewidth = 1.0, drawtype = "lines", smooth = False):
		assert(drawtype in [ "lines", "steps", "points" ])
		if smooth and (drawtype != "lines"):
			raise Exception("Smoothing only possible when drawtype is 'lines'.")
		if color is None:
			color = self._DefaultColors[len(self._datasets) % len(self._DefaultColors)]
		self._datasets.append(self._DataSet(values = data, color = color, title = title, linewidth = linewidth, drawtype = drawtype, smooth = smooth))

	def _plot_command(self, dataset):
		parts = [ ]
		parts += [ "'-' using 1:2" ]
		parts += [ "with %s" % (dataset.drawtype) ]
		if dataset.smooth:
			parts += [ "smooth cspline" ]
		if dataset.title is not None:
			parts += [ "title %s" % (self._stringify(dataset.title)) ]
		parts += [ "lc %s" % (self._stringify(dataset.color)) ]
		parts += [ "lw %.3f" % (dataset.linewidth) ]
		return " ".join(parts)

	def render_gpl(self, f):
		print("set terminal pngcairo size %d,%d" % (self.width, self.height), file = f)
		if self.title is not None:
			print("set title %s" % (self._stringify(self.title)), file = f)
		if self.xlabel is not None:
			print("set xlabel %s" % (self._stringify(self.xlabel)), file = f)
		if self.ylabel is not None:
			print("set ylabel %s" % (self._stringify(self.ylabel)), file = f)
		if not self.ytickmirror:
			print("set ytics nomirror", file = f)
		if self.grid:
			print("set grid", file = f)
		print("plot %s" % (", ".join(self._plot_command(dataset) for dataset in self._datasets)), file = f)
		print(file = f)
		for dataset in self._datasets:
			for (x, y) in dataset.values:
				print("%f %f" % (x, y), file = f)
			print("end", file = f)
			print(file = f)

	def render_png(self, f):
		gpl_f = io.StringIO()
		self.render_gpl(gpl_f)
		png_data = subprocess.check_output([ "gnuplot" ], input = gpl_f.getvalue().encode())
		f.write(png_data)

	def render_pngfile(self, filename):
		with open(filename, "wb") as f:
			self.render_png(f)

if __name__ == "__main__":
	gpl = GnuplotFile()
	gpl.xlabel = "Time (secs)"
	gpl.ylabel = "Data (MiB)"
	gpl.title = "Foo"
	gpl.grid = True
	gpl.ytickmirror = False
	gpl.add_dataset([ (0, 40), (1, 80), (2, 100), (3, 400), (4, 350), (12, 80) ], title = "foo \" bar", linewidth = 2)
	gpl.add_dataset([ (3, 10), (7, 20), (8, 50) ], title = "curve two", linewidth = 2, smooth = True)

	gpl.render_pngfile("x.png")
