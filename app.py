from flask import Flask, render_template, request, redirect, url_for, flash
import subprocess
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

CRON_LOG = "/var/log/syslog"  # Cambia esto si tu log de cron está en otro archivo

def get_crontab():
    try:
        result = subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result.stdout
        else:
            return ""
    except Exception as e:
        return ""

def set_crontab(new_content):
    try:
        proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        proc.communicate(new_content)
        return proc.returncode == 0
    except Exception as e:
        return False

def get_cron_logs():
    try:
        with open(CRON_LOG, "r") as f:
            lines = f.readlines()
        # Filtra solo líneas relacionadas con cron
        cron_lines = [line for line in lines if "CRON" in line or "cron" in line]
        return cron_lines[-100:]  # Últimas 100 líneas
    except Exception as e:
        return ["No se pudo leer el log de cron."]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        new_cron = request.form.get("crontab_content", "")
        if set_crontab(new_cron):
            flash("Crontab actualizado correctamente.", "success")
        else:
            flash("Error al actualizar el crontab.", "danger")
        return redirect(url_for("index"))
    crontab_content = get_crontab()
    return render_template("index.html", crontab_content=crontab_content)

@app.route("/logs")
def logs():
    logs = get_cron_logs()
    return render_template("logs.html", logs=logs)

from flask import jsonify

@app.route("/api/crontab", methods=["POST"])
def api_crontab():
    data = request.get_json()
    lines = data.get("lines", [])
    new_cron = "\n".join(lines)
    success = set_crontab(new_cron)
    if success:
        return jsonify({"success": True, "message": "Crontab actualizado correctamente."})
    else:
        return jsonify({"success": False, "message": "Error al actualizar el crontab."}), 400

@app.route("/api/logs")
def api_logs():
    logs = get_cron_logs()
    return jsonify({"logs": logs})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
