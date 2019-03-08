class RipDrive {
	constructor(overview_div) {
		this._overview_div = overview_div;
		this._drive_div = null;
		this._status_data = null;
		this._progress = null;
	}

	initialize_ui() {
		const that = this;
		const drive_div = document.createElement("div");
		drive_div.classList.add("drive");
		fetch("/static/html/drive.html").then(function(response) {
	        if (response.status == 200) {
				return response.text();
        	}
		}).then(function(template) {
			drive_div.innerHTML = template;

			that._progress = new ProgressBar.Circle(drive_div.querySelector("#progress"), {
				color: "#fcb03c",
				duration: 500,
				easing: "easeInOut",
				strokeWidth: 5,
				step: function(state, circle) {
					var value = Math.round(circle.value() * 100);
					circle.setText(value + "%");
				},
			});

			that._overview_div.append(drive_div);
			that._drive_div = drive_div;
			that.display_status_data();
		});
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
				const drive = new RipDrive(this._overview);
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
		fetch("/status").then(function(response) {
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
