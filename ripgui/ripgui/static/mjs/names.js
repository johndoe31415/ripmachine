/*
	ripmachine - GUI-driven CD/DVD ripper
	Copyright (C) 2019-2019 Johannes Bauer

	This file is part of ripmachine.

	ripmachine is free software; you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation; this program is ONLY licensed under
	version 3 of the License, later versions are explicitly excluded.

	ripmachine is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with ripmachine; if not, write to the Free Software
	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

	Johannes Bauer <JohannesBauer@gmx.de>
*/

class NameTable {
	constructor(base_div) {
		this._base_div = base_div;
	}

	_add_entry(entry) {
		const entry_div = document.createElement("div");
		this._base_div.append(entry_div);
		fetch("/static/html/fragment_entry.html").then(function(response) {
			if (response.status == 200) {
				return response.text();
			}
		}).then(function(entry_template) {
			entry_div.innerHTML = entry_template;
			entry_div.querySelector("#riptime").innerHTML = entry["start_utc"];
			entry_div.querySelector("#ripimg").src = "/api/image/" + entry["ripid"];
		});
	}

	populate(entries) {
		for (const entry of entries) {
			this._add_entry(entry);
		}
	}
}


const name_table = new NameTable(document.querySelector("#content"));

fetch("/api/unnamed").then(function(response) {
	if (response.status == 200) {
		return response.json();
	}
}).then((entries) => name_table.populate(entries));
