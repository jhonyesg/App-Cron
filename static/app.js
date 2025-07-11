let rows = [];
let editIdx = null;

function parseCrontab(content) {
    const lines = content.split('\n');
    return lines.filter(line => line.trim() && !line.trim().startsWith('#')).map(line => {
        const parts = line.trim().split(/\s+/);
        // Soporte para líneas especiales como @reboot, @yearly, etc.
        if (parts[0] && parts[0].startsWith('@')) {
            return [parts[0], '', '', '', '', parts.slice(1).join(' ') || ''];
        }
        if (parts.length < 6) return ["", "", "", "", "", line.trim()];
        return [
            parts[0] || "",
            parts[1] || "",
            parts[2] || "",
            parts[3] || "",
            parts[4] || "",
            parts.slice(5).join(" ") || ""
        ];
    });
}

function loadTaskLog(logPath) {
    fetch(`/api/task-log?log_path=${encodeURIComponent(logPath)}`)
        .then(res => {
            if (!res.ok) {
                throw new Error("No se pudo cargar el log específico.");
            }
            return res.text();
        })
        .then(logContent => {
            const logsPanel = document.getElementById('logsPanel');
            logsPanel.innerHTML = `<div class="logs-title">Log de la tarea</div><pre>${escapeHtml(logContent)}</pre>`;
        })
        .catch(err => {
            const logsPanel = document.getElementById('logsPanel');
            logsPanel.innerHTML = `<div class="logs-title">Log de la tarea</div><pre>${escapeHtml(err.message)}</pre>`;
        });
}

async function executeTaskManually(command) {
    try {
        const res = await fetch("/api/execute-task", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command })
        });
        const data = await res.json();
        if (res.ok) {
            showAlert(data.message, "success");
        } else {
            showAlert(data.message || "Error al ejecutar la tarea.", "danger");
        }
    } catch (error) {
        showAlert("Error al ejecutar la tarea.", "danger");
    }
}

function renderTable() {
    const tbody = document.getElementById('cronTableBody');
    const filter = document.getElementById('filterInput').value.toLowerCase();
    tbody.innerHTML = "";
    rows.forEach((row, idx) => {
        console.log(`Fila ${idx}:`, row);
        const tr = document.createElement('tr');
        for (let i = 0; i < 6; i++) {
            const td = document.createElement('td');
            td.textContent = row[i];
            tr.appendChild(td);
        }
        const tdBtn = document.createElement('td');
        const btnExecute = document.createElement('button');
        btnExecute.type = "button";
        btnExecute.className = "btn btn-outline-success btn-sm";
        btnExecute.innerText = "Ejecutar";
        btnExecute.onclick = () => executeTaskManually(row[5]);
        tdBtn.appendChild(btnExecute);
        tr.appendChild(tdBtn);
        tbody.appendChild(tr);
    });
}

function openModal(idx=null) {
    editIdx = idx;
    const modal = new bootstrap.Modal(document.getElementById('cronModal'));
    if (idx !== null) {
        document.getElementById('cronModalLabel').textContent = "Editar tarea de cron";
        const row = rows[idx];
        // Si es línea especial, solo mostrar el campo minuto y comando, los demás vacíos
        if (row[0] && row[0].startsWith('@')) {
            document.getElementById('modalMin').value = row[0];
            document.getElementById('modalHour').value = "";
            document.getElementById('modalDom').value = "";
            document.getElementById('modalMonth').value = "";
            document.getElementById('modalDow').value = "";
            document.getElementById('modalCmd').value = row[5];
        } else {
            document.getElementById('modalMin').value = row[0];
            document.getElementById('modalHour').value = row[1];
            document.getElementById('modalDom').value = row[2];
            document.getElementById('modalMonth').value = row[3];
            document.getElementById('modalDow').value = row[4];
            document.getElementById('modalCmd').value = row[5];
        }
        document.getElementById('modalDeleteBtn').style.display = "";
    } else {
        document.getElementById('cronModalLabel').textContent = "Nueva tarea de cron";
        document.getElementById('modalMin').value = "*";
        document.getElementById('modalHour').value = "*";
        document.getElementById('modalDom').value = "*";
        document.getElementById('modalMonth').value = "*";
        document.getElementById('modalDow').value = "*";
        document.getElementById('modalCmd').value = "";
        document.getElementById('modalDeleteBtn').style.display = "none";
    }
    modal.show();
}

document.addEventListener("DOMContentLoaded", function() {
    // Inicializar tabla y eventos
    const crontabContent = window.INIT_CRONTAB || "";
    rows = parseCrontab(crontabContent);
    renderTable();

    document.getElementById('modalForm').onsubmit = async function(e) {
        e.preventDefault();
        const min = document.getElementById('modalMin').value.trim();
        const hour = document.getElementById('modalHour').value.trim();
        const dom = document.getElementById('modalDom').value.trim();
        const month = document.getElementById('modalMonth').value.trim();
        const dow = document.getElementById('modalDow').value.trim();
        const cmd = document.getElementById('modalCmd').value.trim();
        // Validación: si es línea especial, solo requiere min y cmd
        if (min.startsWith('@')) {
            if (!min || !cmd) {
                showAlert('Debes completar el campo especial y el comando.', 'danger');
                return;
            }
            var newRow = [min, '', '', '', '', cmd];
        } else {
            // Validación normal
            if (!min || !hour || !dom || !month || !dow || !cmd) {
                showAlert('Debes completar todos los campos.', 'danger');
                return;
            }
            var newRow = [min, hour, dom, month, dow, cmd];
        }
        if (editIdx !== null) {
            rows[editIdx] = newRow;
        } else {
            rows.push(newRow);
        }
        await saveCrontab();
        bootstrap.Modal.getInstance(document.getElementById('cronModal')).hide();
        renderTable();
    };

    document.getElementById('modalDeleteBtn').onclick = async function(e) {
        e.preventDefault();
        if (editIdx !== null) {
            rows.splice(editIdx, 1);
            await saveCrontab();
            bootstrap.Modal.getInstance(document.getElementById('cronModal')).hide();
            renderTable();
        }
    };

    document.getElementById('filterInput').oninput = renderTable;

    // Cargar logs al iniciar
    loadLogs();
    // Recargar logs cada 20s
    setInterval(loadLogs, 20000);
});

async function saveCrontab() {
    const lines = rows
        .map(r => {
            // Si es línea especial, solo toma el primer campo y el comando
            if (r[0] && r[0].startsWith('@')) {
                return r[0] + ' ' + r[5];
            }
            return r.map(x => x.trim()).join(' ');
        })
        .filter(line => line.trim().length > 0);
    // Asegura que el string enviado termina con salto de línea
    let payload = { lines };
    if (lines.length > 0) {
        payload.lines[lines.length - 1] = lines[lines.length - 1] + "\n";
    }
    const res = await fetch("/api/crontab", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (res.ok) {
        showAlert(data.message, "success");
    } else {
        showAlert(data.message || "Error al guardar", "danger");
    }
}

function showAlert(msg, type="success") {
    const alertArea = document.getElementById('alert-area');
    alertArea.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${msg}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
}

async function loadLogs() {
    try {
        const res = await fetch("/api/logs");
        const data = await res.json();
        const logsPanel = document.getElementById('logsPanel');
        if (res.ok && data.logs) {
            logsPanel.innerHTML = `<div class="logs-title">Logs de Cron</div><pre>${data.logs.map(l => escapeHtml(l)).join('\n')}</pre>`;
        } else {
            logsPanel.innerHTML = `<div class="logs-title">Logs de Cron</div><pre>No se pudieron cargar los logs.</pre>`;
        }
    } catch {
        const logsPanel = document.getElementById('logsPanel');
        logsPanel.innerHTML = `<div class="logs-title">Logs de Cron</div><pre>No se pudieron cargar los logs.</pre>`;
    }
}

function escapeHtml(text) {
    return text.replace(/[&<>"']/g, function(m) {
        return ({
            '&': '&',
            '<': '<',
            '>': '>',
            '"': '"',
            "'": '&#39;'
        })[m];
    });
}

console.log(rows);
