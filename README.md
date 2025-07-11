# Gestor Web de Crontab

Este proyecto es una aplicación web desarrollada en Flask para gestionar tareas programadas (crontab) de manera visual y sencilla. Permite agregar, editar, eliminar y visualizar tareas cron, incluyendo tareas especiales como `@reboot`.

## Requisitos
- Python 3.8 o superior
- Linux (recomendado, ya que usa crontab y syslog)
- Acceso a la terminal y permisos para modificar el crontab del usuario

## Instalación y uso

### 1. Clona o descarga el proyecto
Coloca la carpeta del proyecto en cualquier ruta de tu sistema. **No sincronices ni copies el entorno virtual (`venv`) entre equipos.**

### 2. Crea un entorno virtual fuera del proyecto
Esto evita problemas de sincronización y compatibilidad entre equipos.

```bash
python3 -m venv $HOME/.venv_cronapp
```

### 3. Activa el entorno virtual
```bash
source $HOME/.venv_cronapp/bin/activate
```

### 4. Instala las dependencias
Desde la carpeta del proyecto:
```bash
$HOME/.venv_cronapp/bin/pip install -r requirements.txt
```

### 5. Ejecuta la aplicación
Desde la carpeta del proyecto:
```bash
$HOME/.venv_cronapp/bin/python app.py
```
O usa el script:
```bash
bash run_app.sh
```

La aplicación estará disponible en http://localhost:5000

## ¿Cómo eliminar el entorno virtual?
Simplemente borra la carpeta:
```bash
rm -rf $HOME/.venv_cronapp
```

## ¿Cómo desactivar el entorno virtual?
Si lo activaste con `source`, puedes salir con:
```bash
deactivate
```

## Alcance y características
- Gestión visual de tareas cron: agregar, editar, eliminar y duplicar.
- Soporte para tareas especiales (`@reboot`, `@yearly`, etc.).
- Visualización de logs recientes de cron.
- Filtros y búsqueda rápida.
- No requiere instalar nada en el sistema global, todo se maneja en el entorno virtual.
- El entorno virtual es local a cada equipo, no se sincroniza ni comparte.
- El proyecto es portable: solo necesitas el código fuente y `requirements.txt`.

## Notas importantes
- No subas ni sincronices la carpeta del entorno virtual (`.venv_cronapp` o `venv`).
- Cada usuario debe crear su propio entorno virtual localmente.
- El proyecto está pensado para sistemas Linux.
- Para que los cambios en el crontab tengan efecto, el usuario debe tener permisos para modificar su propio crontab.

---

**Autor:** Tu nombre aquí
**Licencia:** MIT
