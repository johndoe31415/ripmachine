class RipDrive {
	constructor(drive_id, overview_div) {
		this._drive_id = drive_id;
		this._overview_div = overview_div;
		this._drive_div = null;
		this._status_data = null;
		this._progress = null;
	}

	_on_prepare() {
		console.log("prepare " + this._drive_id);
		drive_div.querySelector("#imagefile");
	}

	_on_start() {
		console.log("start " + this._drive_id);
		fetch("/api/start/" + this._drive_id);
	}

	_on_stop() {
		console.log("stop " + this._drive_id);
		fetch("/api/abort/" + this._drive_id);
	}

	_on_open() {
		console.log("open " + this._drive_id);
		fetch("/api/open/" + this._drive_id);
	}

	_on_close() {
		console.log("close " + this._drive_id);
		fetch("/api/close/" + this._drive_id);
	}

	_on_clear() {
		console.log("clear " + this._drive_id);
		fetch("/api/clear/" + this._drive_id);
	}

	_recv_template(drive_div, template) {
		drive_div.innerHTML = template;

		this._progress = new ProgressBar.Circle(drive_div.querySelector("#progress"), {
			color: "#fcb03c",
			duration: 500,
			easing: "easeInOut",
			strokeWidth: 5,
			step: function(state, circle) {
				var value = Math.round(circle.value() * 100);
				circle.setText(value + "%");
			},
		});

//		drive_div.querySelector("#imagefile");
		drive_div.querySelector("#btn_prepare").addEventListener("click", () => this._on_prepare());
		drive_div.querySelector("#btn_start").addEventListener("click", () => this._on_start());
		drive_div.querySelector("#btn_stop").addEventListener("click", () => this._on_stop());
		drive_div.querySelector("#btn_open").addEventListener("click", () => this._on_open());
		drive_div.querySelector("#btn_close").addEventListener("click", () => this._on_close());
		drive_div.querySelector("#btn_clear").addEventListener("click", () => this._on_clear());

		this.display_status_data();

		this._drive_div = drive_div;

		this._set_status_icon("");
		this.display_status_data();
	}

	initialize_ui() {
		const drive_div = document.createElement("div");
		drive_div.classList.add("drive");
		this._overview_div.append(drive_div);

		fetch("/static/html/drive.html").then(function(response) {
	        if (response.status == 200) {
				return response.text();
        	}
		}).then((template) => this._recv_template(drive_div, template));
	}

	_set_status_icon(icon_name) {
		this._drive_div.querySelectorAll(".icon").forEach(function(element) {
			element.style.display = "none";
		});
		const icon = this._drive_div.querySelector(".icon-" + icon_name);
		if (icon) {
			icon.style.display = "";
		}
	}

	display_status_data() {
		if (!this._status_data || !this._drive_div) {
			return;
		}

		console.log(this._status_data);

		this._drive_div.querySelector("#drive_id").innerHTML = this._status_data["name"];
		let ratio = (this._status_data["data"] == 0) ? 0 : (this._status_data["progress"] / this._status_data["data"]);
		if (ratio > 1) {
			ratio = 1;
		}
		this._progress.animate(ratio);

		const action_span = this._drive_div.querySelector("#action");
		if (this._status_data["status"] == "idle") {
			this._set_status_icon("ok");
			action_span.innerHTML = "idle";
		} else if (this._status_data["status"] == "running") {
			this._set_status_icon("run");
			action_span.innerHTML = "running";
			if (this._status_data["track"] != null) {
				action_span.innerHTML += ", track " + this._status_data["track"][0] + " of " + this._status_data["track"][1];

			}
			action_span.innerHTML += sprintf(", speed %.0f kB/s", this._status_data["speed"] / 1024);
			action_span.innerHTML += sprintf(", %.0f MB of %.0f MB", this._status_data["progress"] / 1024 / 1024, this._status_data["data"] / 1024 / 1024);
		} else if (this._status_data["status"] == "aborted") {
			this._set_status_icon("err");
			action_span.innerHTML = "aborted";
		} else if (this._status_data["status"] == "errored") {
			this._set_status_icon("err");
			action_span.innerHTML = "error: " + this._status_data["error"];
		} else if (this._status_data["status"] == "completed") {
			this._set_status_icon("ok");
			action_span.innerHTML = "completed";
		} else {
			this._set_status_icon("undefined");
			action_span.innerHTML = "undefined";
		}
	}

	update_status_data(data) {
		this._status_data = data;
		this.display_status_data();
	}
}

class RipGUI {
	constructor(overview_div) {
		this._overview = overview_div;
		this._drives = null;
	}

	_recv_status(status_doc) {
		if (this._drives == null) {
			this._drives = [ ];
			for (const drive_id in status_doc["drives"]) {
				const drive = new RipDrive(drive_id, this._overview);
				drive.initialize_ui();
				this._drives.push(drive);
			}
		}
		for (const drive_id in status_doc["drives"]) {
			this._drives[drive_id].update_status_data(status_doc["drives"][drive_id]);
		}
	}

	update_status() {
		const that = this;
		fetch("/api/status").then(function(response) {
	        if (response.status == 200) {
				return response.json();
        	}
		}).then((status_doc) => this._recv_status(status_doc));
	}
}

const overview_div = document.querySelector("#overview");
const ripgui = new RipGUI(overview_div);
ripgui.update_status();
setInterval(() => ripgui.update_status(), 2500);
