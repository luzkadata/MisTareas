# Proyecto: Mis Tareas

## Estructura de carpetas

```
📁 Claude/
   ├── 📄 notas_flotante.py       ← Código fuente de la aplicación
   ├── 🖼️  icon.ico                ← Ícono de la aplicación
   ├── 📋 tareas.json             ← Tareas guardadas (desarrollo)
   └── 📁 dist/
       ├── 🚀 MisTareas.exe       ← Aplicación ejecutable final
       └── 📋 tareas.json         ← Tareas guardadas (producción)
```

---

## Descripción del proyecto

Aplicación de escritorio flotante para gestión de tareas personales.
Siempre visible sobre otras ventanas, inspirada en Microsoft To Do.

---

## Funcionalidades

- [x] Agregar, completar y eliminar tareas
- [x] Etiquetas: Urgente, Importante, No urgente, No importante
- [x] Programar fecha y hora opcional por tarea
- [x] Editar etiqueta y fecha de tareas existentes
- [x] Persistencia de tareas (sobrevive al apagar el PC)
- [x] Minimizar a bandeja del sistema
- [x] Ícono personalizado
- [x] Redimensionable y arrastrable
- [x] Compatible con cualquier PC Windows (sin instalar Python)

---

## Tecnologías usadas

| Tecnología   | Uso                              |
|--------------|----------------------------------|
| Python 3.13  | Lenguaje principal               |
| tkinter      | Interfaz gráfica                 |
| pystray      | Bandeja del sistema              |
| Pillow       | Generación del ícono             |
| PyInstaller  | Compilación a .exe               |
| JSON         | Almacenamiento de tareas         |

---

## Notas

- Para recompilar el `.exe` ejecutar desde la carpeta del proyecto:
  ```bash
  python -m PyInstaller --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --name "MisTareas" notas_flotante.py
  ```
- Al copiar la app a otro PC, incluir `MisTareas.exe` + `icon.ico`
- El archivo `tareas.json` se crea automáticamente al agregar la primera tarea
