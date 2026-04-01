# 📋 Mis Tareas

Aplicación de escritorio flotante para gestión de tareas personales, inspirada en Microsoft To Do.
Siempre visible sobre otras ventanas mientras trabajas.

---

## ✨ Funcionalidades

- Agregar, completar y eliminar tareas
- Etiquetas por tarea: **Urgente**, **Importante**, **No urgente**, **No importante**
- Programar **fecha y hora** opcional por tarea
- **Editar** etiqueta y fecha de tareas existentes
- Tareas **persistentes** (se mantienen al apagar el PC)
- Se **minimiza a la bandeja** del sistema (junto al reloj)
- Ventana **arrastrable** y **redimensionable**
- Ejecutable `.exe` — no requiere instalar Python

---

## 🖥️ Captura

> Widget flotante siempre visible con diseño inspirado en Microsoft To Do.

---

## 🚀 Cómo ejecutar

### Opción 1 — Ejecutable directo (Windows)
Descarga `MisTareas.exe` desde la sección [Releases](../../releases) y ejecútalo.
No necesitas instalar nada.

### Opción 2 — Desde el código fuente
Requiere Python 3.10+

```bash
# Instalar dependencias
pip install pystray pillow

# Ejecutar
python notas_flotante.py
```

---

## 🔧 Compilar el ejecutable

```bash
pip install pyinstaller pillow pystray

python -m PyInstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --name "MisTareas" notas_flotante.py
```

El ejecutable quedará en la carpeta `dist/`.

---

## 🗂️ Estructura del proyecto

```
📁 Claude/
   ├── 📄 notas_flotante.py    ← Código fuente
   ├── 🖼️  icon.ico             ← Ícono de la app
   ├── 📋 estructura.md        ← Documentación de carpetas
   ├── 📄 README.md            ← Este archivo
   └── 📄 .gitignore           ← Archivos ignorados por Git
```

---

## 🛠️ Tecnologías

| Tecnología  | Uso                    |
|-------------|------------------------|
| Python 3.13 | Lenguaje principal     |
| tkinter     | Interfaz gráfica       |
| pystray     | Bandeja del sistema    |
| Pillow      | Generación del ícono   |
| PyInstaller | Compilación a `.exe`   |
| JSON        | Almacenamiento local   |

---

## 📝 Notas

- El archivo `tareas.json` se crea automáticamente al agregar la primera tarea.
- Al copiar el `.exe` a otro PC, incluye también el `icon.ico` en la misma carpeta.

---

*Desarrollado con Python + tkinter*
