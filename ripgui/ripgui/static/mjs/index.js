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

		drive_div.querySelector("#imagefile");
		drive_div.querySelector("#btn_prepare").addEventListener("click", () => this._on_prepare());
		drive_div.querySelector("#btn_start").addEventListener("click", () => this._on_start());
		drive_div.querySelector("#btn_stop").addEventListener("click", () => this._on_stop());
		drive_div.querySelector("#btn_open").addEventListener("click", () => this._on_open());
		drive_div.querySelector("#btn_close").addEventListener("click", () => this._on_close());

		this.display_status_data();

		this._drive_div = drive_div;
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

	display_status_data() {
		if (!this._status_data || !this._drive_div) {
			return;
		}

		this._drive_div.querySelector("#drive_id").innerHTML = this._status_data["name"];
		let ratio = (this._status_data["data"] == 0) ? 0 : (this._status_data["progress"] / this._status_data["data"]);
		if (ratio > 1) {
			ratio = 1;
		}
		this._progress.animate(ratio);
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
