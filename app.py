from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
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

@app.route("/api/task-log", methods=["GET"])
def api_task_log():
    log_path = request.args.get("log_path")
    if not log_path or not os.path.exists(log_path):
        return jsonify({"success": False, "message": "Archivo de log no encontrado."}), 404
    try:
        return send_file(log_path, mimetype="text/plain")
    except Exception as e:
        return jsonify({"success": False, "message": "Error al leer el archivo de log."}), 500

@app.route("/api/execute-task", methods=["POST"])
def api_execute_task():
    data = request.get_json()
    command = data.get("command")
    if not command:
        return jsonify({"success": False, "message": "Comando no proporcionado."}), 400
    try:
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return jsonify({"success": True, "message": "Tarea ejecutada correctamente."})
        else:
            return jsonify({"success": False, "message": f"Error al ejecutar la tarea: {result.stderr}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": "Error interno al ejecutar la tarea."}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
