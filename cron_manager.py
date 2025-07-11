import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import re
import tempfile

class CronManagerApp:
    LOG_DIR = os.path.expanduser('~/logs')
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Tareas Cron")
        self.root.geometry("800x650")
        self.cron_txt = "cron_jobs.txt"
        # Crear carpeta de logs si no existe, con print de estado
        try:
            if not os.path.exists(self.LOG_DIR):
                os.makedirs(self.LOG_DIR, exist_ok=True)
                print(f"[INFO] Carpeta de logs creada: {self.LOG_DIR}")
            else:
                print(f"[INFO] Carpeta de logs ya existe: {self.LOG_DIR}")
        except Exception as e:
            print(f"[ERROR] No se pudo crear la carpeta de logs: {e}")
        
        # Try to use custom logo if available
        try:
            self.root.iconphoto(False, tk.PhotoImage(file='cron_logo.png'))
        except:
            pass
        
        self.create_widgets()
        self.load_cron_jobs()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        xscroll = ttk.Scrollbar(main_frame, orient='horizontal')
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        yscroll = ttk.Scrollbar(main_frame, orient='vertical')
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview for cron jobs (add 'Descripción')
        self.tree = ttk.Treeview(main_frame, columns=('Descripcion', 'Schedule', 'Command', 'Log'), show='headings', xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
        self.tree.heading('Descripcion', text='Descripción')
        self.tree.heading('Schedule', text='Programación')
        self.tree.heading('Command', text='Comando')
        self.tree.heading('Log', text='Archivo Log')
        self.tree.column('Descripcion', width=180)
        self.tree.column('Schedule', width=110)
        self.tree.column('Command', width=350)
        self.tree.column('Log', width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        xscroll.config(command=self.tree.xview)
        yscroll.config(command=self.tree.yview)

        # Preview area
        ttk.Label(main_frame, text="Previsualización Cron:").pack(anchor=tk.W)
        self.preview_var = tk.StringVar()
        preview_entry = ttk.Entry(main_frame, textvariable=self.preview_var, state='readonly', width=80)
        preview_entry.pack(fill=tk.X, pady=(0, 10))

        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="Agregar", command=self.add_job).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.edit_job).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_job).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Duplicar", command=self.duplicate_job).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Ejecutar Ahora", command=self.run_job).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar Cambios", command=self.save_cron_jobs).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Actualizar", command=self.load_cron_jobs).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Ver Log", command=self.view_log).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var.set("Listo")
        
        # Update preview when selection changes
        self.tree.bind("<<TreeviewSelect>>", self.update_preview)
    
    def update_preview(self, event=None):
        selected = self.tree.selection()
        if selected:
            desc, schedule, command, log_file = self.tree.item(selected[0], 'values')
            preview = f"{schedule} {command}"
            if log_file:
                preview += f" >> {self.LOG_DIR}/{log_file} 2>&1"
            self.preview_var.set(preview)
        else:
            self.preview_var.set("")
            
    def load_cron_jobs(self):
        self.tree.delete(*self.tree.get_children())
        job_count = 0
        print(f"[DEBUG] Leyendo crontab del sistema para usuario: {os.getlogin()}")
        # Leer directamente del crontab del sistema
        try:
            with os.popen('crontab -l') as f:
                found = False
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Ajustar la expresión regular para manejar diferentes formatos
                    m = re.match(r'^(\S+\s+\S+\s+\S+\s+\S+\s+\S+)\s+(.*?)(?:\s+>>\s+/var/log/(\S+)\s+2>&1)?$', line)
                    if m:
                        found = True
                        schedule, command, log_file = m.groups()
                        log_file = log_file if log_file else ''
                        desc = self.cron_human_readable(schedule)
                        print(f"[DEBUG] Cargado: {schedule} | {command} | {log_file}")
                        # En la tabla principal, mostrar: descripcion, programacion (schedule), comando, log_file
                        self.tree.insert('', 'end', values=(desc, schedule, command, log_file))
                        job_count += 1
                if not found:
                    print("[DEBUG] No se encontraron registros válidos en el crontab.")
        except Exception as e:
            print(f"[ERROR] Error al leer el crontab: {str(e)}")
            messagebox.showerror("Error", f"Error al leer el crontab: {str(e)}")
        print(f"[DEBUG] Total cargados: {job_count}")
        self.status_var.set(f"Cargados {job_count} trabajos cron del sistema")

    def cron_human_readable(self, schedule):
        # Descripción mejorada para distinguir entre '20 * * * *' y '*/20 * * * *'
        parts = schedule.split()
        if len(parts) != 5:
            return schedule
        min_, hour, dom, mon, dow = parts
        # Cada minuto
        if min_ == '*' and hour == '*' and dom == '*' and mon == '*' and dow == '*':
            return 'Cada minuto'
        # Cada N minutos (*/N)
        if re.match(r'^\*/(\d+)$', min_) and hour == '*' and dom == '*' and mon == '*' and dow == '*':
            return f"Cada {min_[2:]} minutos"
        # Minuto N de cada hora (N * * * *)
        if re.match(r'^\d+$', min_) and hour == '*' and dom == '*' and mon == '*' and dow == '*':
            return f"Una vez por hora, minuto {min_}"
        # Cada N horas
        if min_ == '0' and re.match(r'^\*/(\d+)$', hour) and dom == '*' and mon == '*' and dow == '*':
            return f"Cada {hour[2:]} horas"
        # Diario a una hora y minuto específico
        if re.match(r'^\d+$', min_) and re.match(r'^\d+$', hour) and dom == '*' and mon == '*' and dow == '*':
            return f"Diario a las {hour.zfill(2)}:{min_.zfill(2)}"
        # Cada semana en un día específico
        if re.match(r'^\d+$', min_) and re.match(r'^\d+$', hour) and dom == '*' and mon == '*' and dow != '*':
            return f"Semanal ({dow}) a las {hour.zfill(2)}:{min_.zfill(2)}"
        # Cada mes en un día específico
        if re.match(r'^\d+$', min_) and re.match(r'^\d+$', hour) and re.match(r'^\d+$', dom) and mon == '*' and dow == '*':
            return f"Mensual el día {dom} a las {hour.zfill(2)}:{min_.zfill(2)}"
        # Si solo hora es número y el resto son '*', cada día a esa hora
        if min_ == '0' and re.match(r'^\d+$', hour) and dom == '*' and mon == '*' and dow == '*':
            return f"Cada día a las {hour.zfill(2)}:00"
        # Si hay más de un campo numérico, mostrar todos
        campos = []
        if re.match(r'^\d+$', min_):
            campos.append(f"{min_} minutos")
        if re.match(r'^\d+$', hour):
            campos.append(f"{hour} horas")
        if re.match(r'^\d+$', dom):
            campos.append(f"día {dom}")
        if re.match(r'^\d+$', mon):
            campos.append(f"mes {mon}")
        if re.match(r'^\d+$', dow):
            campos.append(f"día de semana {dow}")
        if campos:
            return "Cada " + " y ".join(campos)
        # Si no coincide, mostrar schedule original
        return schedule

    def view_log(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Seleccione un trabajo para ver el log")
            return
        log_file = self.tree.item(selected[0], 'values')[3]
        if not log_file:
            messagebox.showinfo("Sin log", "Este trabajo no tiene log configurado.")
            return
        log_path = os.path.join(self.LOG_DIR, log_file)
        if not os.path.exists(log_path):
            messagebox.showerror("No existe el log", f"No se encontró el archivo: {log_path}")
            return
        # Abrir ventana de tail -f
        win = tk.Toplevel(self.root)
        win.title(f"Log: {log_file}")
        text = tk.Text(win, wrap='none', height=25, width=100)
        text.pack(fill=tk.BOTH, expand=True)
        def tail():
            p = subprocess.Popen(['tail', '-f', log_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for line in iter(p.stdout.readline, ''):
                text.insert(tk.END, line)
                text.see(tk.END)
                win.update()
        import threading
        threading.Thread(target=tail, daemon=True).start()
    
    def save_cron_jobs(self):
        try:
            os.makedirs(self.LOG_DIR, exist_ok=True)
            with open(self.cron_txt, 'w') as f:
                lines = []
                for item in self.tree.get_children():
                    desc, schedule, command, log_file = self.tree.item(item, 'values')
                    # Construir línea de cron real
                    cron_line = f"{schedule} {command} >> {self.LOG_DIR}/{log_file} 2>&1"
                    lines.append(cron_line)
                    f.write(f"{schedule}|{command}|{log_file}\n")
            # Escribir en el crontab del usuario
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp:
                temp.write('\n'.join(lines) + '\n')
                temp_path = temp.name
            os.system(f'crontab {temp_path}')
            os.remove(temp_path)
            job_count = len(self.tree.get_children())
            self.status_var.set(f"Guardados {job_count} trabajos cron y actualizado crontab del sistema")
            messagebox.showinfo("Éxito", "¡Trabajos cron guardados y crontab actualizado!")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar trabajos cron: {str(e)}")
            self.status_var.set("Error al guardar trabajos cron")
    
    def run_job(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a cron job to run")
            return
        command = self.tree.item(selected[0], 'values')[2]
        log_file = self.tree.item(selected[0], 'values')[3]
        log_path = os.path.join(self.LOG_DIR, log_file) if log_file else None
        # Mensaje informativo sobre el log
        if log_path:
            if os.path.exists(log_path):
                print(f"[INFO] El archivo de log ya existe: {log_path}")
            else:
                print(f"[INFO] El archivo de log NO existe, se creará: {log_path}")
            os.makedirs(self.LOG_DIR, exist_ok=True)
            command_line = f"{command} 2>&1 | tee -a '{log_path}'"
        else:
            command_line = command
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.sh') as f:
            f.write(f'''#!/bin/bash\n{command_line}\necho "Job completed. Press Enter to exit..."\nread\nrm -f "$0"  # Delete self after execution\n''')
            script_path = f.name
        os.chmod(script_path, 0o755)
        subprocess.Popen(['x-terminal-emulator', '-e', script_path])
    
    def add_job(self):
        AddEditDialog(self.root, self)
    
    def edit_job(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a cron job to edit")
            return
        values = self.tree.item(selected[0], 'values')
        # Solo pasar los valores reales: schedule, command, log_file
        real_values = (None, values[1], values[2], values[3])
        AddEditDialog(self.root, self, selected[0], real_values)
    
    def delete_job(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección requerida", "Por favor seleccione un trabajo cron para eliminar")
            return
        if messagebox.askyesno("Confirmar eliminación", "¿Está seguro de que desea eliminar este trabajo cron?"):
            self.tree.delete(selected[0])
            self.status_var.set("Trabajo cron eliminado correctamente")
    
    def duplicate_job(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a cron job to duplicate")
            return
        values = self.tree.item(selected[0], 'values')
        self.tree.insert('', 'end', values=values)
    
    # run_job method was moved up earlier in the file

class AddEditDialog(tk.Toplevel):
    def __init__(self, parent, app, item_id=None, values=None):
        super().__init__(parent)
        self.app = app
        self.item_id = item_id
        self.transient(parent)
        self.grab_set()
        
        self.title("Editar Tarea Cron" if item_id else "Agregar Tarea Cron")
        self.geometry("500x400")
        
        self.create_widgets()
        if values:
            self.load_values(values)
    
    def create_widgets(self):
        # Crear el marco principal
        self.main_frame = ttk.Frame(self, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Campos de entrada para los 5 campos de cron
        labels = ["Minuto", "Hora", "Día del mes", "Mes", "Día de la semana"]
        self.cron_vars = [tk.StringVar(value="*") for _ in range(5)]
        for i, label in enumerate(labels):
            ttk.Label(self.main_frame, text=label+":").grid(row=i, column=0, sticky=tk.W, pady=5)
            ttk.Entry(self.main_frame, textvariable=self.cron_vars[i], width=10).grid(row=i, column=1, sticky=tk.EW, padx=(0, 5), pady=5)

        # Comando
        ttk.Label(self.main_frame, text="Comando:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.command = ttk.Entry(self.main_frame)
        self.command.grid(row=5, column=1, sticky=tk.EW, padx=(0, 5), pady=5)

        # Log file
        ttk.Label(self.main_frame, text="Nombre del Log:").grid(row=6, column=0, sticky=tk.W, pady=5)
        log_frame = ttk.Frame(self.main_frame)
        log_frame.grid(row=6, column=1, sticky=tk.EW, padx=(0, 5), pady=5)
        self.log_file = ttk.Entry(log_frame)
        self.log_file.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(log_frame, text=".log").pack(side=tk.LEFT, padx=5)

        # Preview label
        ttk.Label(self.main_frame, text="Ruta completa:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.full_log_path = ttk.Label(self.main_frame, text=f"{CronManagerApp.LOG_DIR}/")
        self.full_log_path.grid(row=7, column=1, sticky=tk.W, padx=(0, 5), pady=5)

        # Update log preview when typing
        self.log_file.bind("<KeyRelease>", self.update_log_preview)

        # Botones
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Guardar", command=self.save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

        # Configurar pesos de la cuadrícula
        self.main_frame.columnconfigure(1, weight=1)

    def update_log_preview(self, event=None):
        log_name = self.log_file.get()
        self.full_log_path.config(text=f"{CronManagerApp.LOG_DIR}/{log_name}.log")
    
    def load_values(self, values):
        # Set schedule fields
        schedule = values[1]  # Usar la columna 'Programación' (schedule) real
        parts = schedule.split()
        for i in range(5):
            self.cron_vars[i].set(parts[i] if i < len(parts) else "*")
        # Set command
        self.command.delete(0, tk.END)
        self.command.insert(0, values[2])
        # Set log file (quitar .log si lo tiene)
        log_name = values[3]
        if log_name.endswith('.log'):
            log_name = log_name[:-4]
        self.log_file.delete(0, tk.END)
        self.log_file.insert(0, log_name)
        self.update_log_preview()

    def save(self):
        # Validar inputs
        if not self.command.get():
            messagebox.showerror("Error", "Se requiere un comando")
            return
        if not self.log_file.get():
            messagebox.showerror("Error", "Se requiere un nombre para el archivo log")
            return
        # Construir schedule desde los 5 campos
        parts = [v.get().strip() or '*' for v in self.cron_vars]
        # Si el usuario pone solo un número en minuto y los demás son '*', convertir automáticamente a '*/N'
        if re.match(r'^\d+$', parts[0]) and all(p == '*' for p in parts[1:]):
            parts[0] = f"*/{parts[0]}"
        schedule = ' '.join(parts)
        command = self.command.get()
        log_file = self.log_file.get()
        log_file_display = f"{log_file}.log" if log_file else ''
        desc = self.app.cron_human_readable(schedule)
        values = (desc, schedule, command, log_file_display)
        if len(schedule.split()) != 5:
            messagebox.showerror("Programación Inválida", "El formato de programación debe tener 5 campos.")
            return
        if self.item_id:
            self.app.tree.item(self.item_id, values=values)
        else:
            self.app.tree.insert('', 'end', values=values)
        self.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CronManagerApp(root)
    root.mainloop()
