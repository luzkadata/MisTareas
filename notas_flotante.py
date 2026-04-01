import tkinter as tk
from tkinter import TclError
import json
import os
import sys
import threading
from datetime import datetime
from PIL import Image, ImageDraw
import pystray

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ICON_PATH = os.path.join(BASE_DIR, "icon.ico")

ARCHIVO = os.path.join(BASE_DIR, "tareas.json")

# ── Paleta Microsoft To Do ────────────────────────────────────────────────────
HDR     = "#5b5fc7"   # azul-violeta del header
BG      = "#e8f4fb"   # fondo celeste claro
SURF    = "#d6ecf7"   # superficie inputs / opts
BORDER  = "#b8d9ed"   # bordes sutiles
ACCENT  = "#5b5fc7"   # acento igual al header
FG      = "#242424"   # texto principal
FG2     = "#605e5c"   # texto secundario
FG3     = "#a19f9d"   # texto atenuado / placeholder
RED     = "#d13438"
GREEN   = "#107c10"
ORANGE  = "#ca5010"

ETIQUETAS = {
    "Urgente":       {"bg": "#fde7e9", "fg": "#d13438"},
    "Importante":    {"bg": "#fff4ce", "fg": "#ca5010"},
    "No urgente":    {"bg": "#dff6dd", "fg": "#107c10"},
    "No importante": {"bg": "#f0f0f0", "fg": "#a19f9d"},
}


class Tarea:
    def __init__(self, texto, hecha=False, fecha=None, etiqueta=None):
        self.texto    = texto
        self.hecha    = hecha
        self.fecha    = fecha
        self.etiqueta = etiqueta


class DateTimePicker(tk.Toplevel):
    MESES    = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    DIAS_SEM = ["Lu","Ma","Mi","Ju","Vi","Sá","Do"]

    def __init__(self, parent, callback, initial=None):
        super().__init__(parent)
        self.callback = callback
        self.overrideredirect(True)
        self.configure(bg=BORDER)
        self.wm_attributes("-topmost", True)

        now = initial or datetime.now()
        self._year  = tk.IntVar(value=now.year)
        self._month = tk.IntVar(value=now.month)
        self._day   = tk.IntVar(value=now.day)
        self._hour  = tk.StringVar(value=f"{now.hour:02d}")
        self._min   = tk.StringVar(value=f"{now.minute:02d}")

        self._build()
        self._draw_calendar()

        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()//2 - self.winfo_width()//2
        py = parent.winfo_rooty() + parent.winfo_height()//2 - self.winfo_height()//2
        self.geometry(f"+{px}+{py}")
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # Cabecera
        hdr = tk.Frame(outer, bg=HDR, height=38)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Programar fecha y hora", bg=HDR, fg="#ffffff",
                 font=("Segoe UI", 9), padx=12).pack(side="left", fill="y")
        tk.Button(hdr, text="×", bg=HDR, fg="#ffffff", relief="flat",
                  font=("Segoe UI", 13), cursor="hand2",
                  activebackground=HDR, activeforeground="#ffffff",
                  command=self.destroy).pack(side="right", padx=4)

        # Navegación mes/año
        nav = tk.Frame(outer, bg=BG, pady=8)
        nav.pack(fill="x", padx=12)
        tk.Button(nav, text="‹", bg=BG, fg=FG2, relief="flat",
                  font=("Segoe UI", 14), cursor="hand2",
                  activebackground=SURF,
                  command=lambda: self._cambiar_mes(-1)).pack(side="left")
        self.lbl_mes = tk.Label(nav, text="", bg=BG, fg=FG,
                                font=("Segoe UI", 10, "bold"), width=14)
        self.lbl_mes.pack(side="left", expand=True)
        tk.Button(nav, text="›", bg=BG, fg=FG2, relief="flat",
                  font=("Segoe UI", 14), cursor="hand2",
                  activebackground=SURF,
                  command=lambda: self._cambiar_mes(1)).pack(side="right")

        # Calendario
        self.cal_frame = tk.Frame(outer, bg=BG)
        self.cal_frame.pack(padx=12, pady=(0, 8))

        # Hora
        tf = tk.Frame(outer, bg=SURF, pady=8,
                      highlightthickness=1, highlightbackground=BORDER)
        tf.pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(tf, text="Hora", bg=SURF, fg=FG2,
                 font=("Segoe UI", 9), padx=8).pack(side="left")
        self._spin(tf, self._hour, 0, 23)
        tk.Label(tf, text=":", bg=SURF, fg=FG,
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        self._spin(tf, self._min, 0, 59)

        # Botones
        br = tk.Frame(outer, bg=BG, pady=8)
        br.pack(fill="x", padx=12)
        tk.Button(br, text="Sin fecha", bg=BG, fg=FG3,
                  relief="flat", font=("Segoe UI", 9), cursor="hand2",
                  activebackground=SURF,
                  command=self._sin_fecha).pack(side="left")
        tk.Button(br, text="Confirmar", bg=ACCENT, fg="#ffffff",
                  relief="flat", font=("Segoe UI", 9, "bold"), cursor="hand2",
                  padx=14, pady=5, command=self._confirmar).pack(side="right")

    def _spin(self, parent, var, mn, mx):
        tk.Spinbox(parent, textvariable=var, from_=mn, to=mx,
                   width=3, bg=SURF, fg=FG, buttonbackground=SURF,
                   insertbackground=FG, relief="flat",
                   font=("Segoe UI", 12), highlightthickness=0,
                   command=lambda v=var, lo=mn, hi=mx: self._norm(v, lo, hi)
                   ).pack(side="left", padx=3)

    def _norm(self, var, lo, hi):
        try:
            val = max(lo, min(hi, int(var.get())))
            var.set(f"{val:02d}")
        except ValueError:
            var.set(f"{lo:02d}")

    def _cambiar_mes(self, delta):
        m, y = self._month.get() + delta, self._year.get()
        if m > 12: m, y = 1, y + 1
        elif m < 1: m, y = 12, y - 1
        self._month.set(m); self._year.set(y)
        self._draw_calendar()

    def _draw_calendar(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()
        y, m = self._year.get(), self._month.get()
        self.lbl_mes.config(text=f"{self.MESES[m-1]}  {y}")

        for c, d in enumerate(self.DIAS_SEM):
            tk.Label(self.cal_frame, text=d, bg=BG, fg=FG3,
                     font=("Segoe UI", 8, "bold"), width=3
                     ).grid(row=0, column=c, pady=(0, 4))

        import calendar
        primer_dia, total = calendar.monthrange(y, m)
        row, col = 1, primer_dia
        hoy = datetime.now()

        for dia in range(1, total + 1):
            es_hoy = (dia == hoy.day and m == hoy.month and y == hoy.year)
            es_sel = dia == self._day.get()
            if es_sel:
                bg_b, fg_b = ACCENT, "#ffffff"
            elif es_hoy:
                bg_b, fg_b = "#ebe9f8", ACCENT
            else:
                bg_b, fg_b = BG, FG2

            tk.Button(self.cal_frame, text=str(dia), width=3,
                      bg=bg_b, fg=fg_b, relief="flat",
                      font=("Segoe UI", 9), cursor="hand2",
                      activebackground="#ebe9f8", activeforeground=ACCENT,
                      command=lambda d=dia: self._sel_dia(d)
                      ).grid(row=row, column=col, padx=1, pady=1)
            col += 1
            if col > 6: col, row = 0, row + 1

    def _sel_dia(self, dia):
        self._day.set(dia)
        self._draw_calendar()

    def _confirmar(self):
        try:
            dt = datetime(self._year.get(), self._month.get(), self._day.get(),
                          int(self._hour.get()), int(self._min.get()))
            self.callback(dt)
        except (ValueError, TclError):
            pass
        self.destroy()

    def _sin_fecha(self):
        self.callback(None)
        self.destroy()


class EditPopup(tk.Toplevel):
    """Popup para editar etiqueta y fecha de una tarea existente."""

    def __init__(self, parent, tarea: "Tarea", callback):
        super().__init__(parent)
        self.tarea    = tarea
        self.callback = callback
        self.overrideredirect(True)
        self.configure(bg=BORDER)
        self.wm_attributes("-topmost", True)

        self._fecha     = tarea.fecha
        self._etiqueta  = tarea.etiqueta

        self._build()

        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()//2 - self.winfo_width()//2
        py = parent.winfo_rooty() + parent.winfo_height()//2 - self.winfo_height()//2
        self.geometry(f"+{px}+{py}")
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # Cabecera
        hdr = tk.Frame(outer, bg=HDR, height=38)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        titulo = (self.tarea.texto[:30] + "…") if len(self.tarea.texto) > 30 else self.tarea.texto
        tk.Label(hdr, text=f"Editar · {titulo}", bg=HDR, fg="#ffffff",
                 font=("Segoe UI", 9), padx=12).pack(side="left", fill="y")
        tk.Button(hdr, text="×", bg=HDR, fg="#c8c6f7", relief="flat",
                  font=("Segoe UI", 13), cursor="hand2",
                  activebackground=HDR, activeforeground="#ffffff",
                  command=self.destroy).pack(side="right", padx=4)

        # ── Etiqueta ──
        tk.Label(outer, text="Etiqueta", bg=BG, fg=FG2,
                 font=("Segoe UI", 8, "bold"), anchor="w", padx=12
                 ).pack(fill="x", pady=(10, 4))

        etiq_frame = tk.Frame(outer, bg=BG, padx=12)
        etiq_frame.pack(fill="x")

        self._btns_etq = {}
        for nombre, colores in ETIQUETAS.items():
            btn = tk.Button(etiq_frame, text=nombre,
                            bg=SURF, fg=FG3,
                            relief="flat", font=("Segoe UI", 8),
                            cursor="hand2", padx=6, pady=3,
                            command=lambda n=nombre: self._sel_etq(n))
            btn.pack(side="left", padx=2)
            self._btns_etq[nombre] = btn

        # Botón quitar etiqueta
        tk.Button(etiq_frame, text="Ninguna", bg=BG, fg=FG3,
                  relief="flat", font=("Segoe UI", 8), cursor="hand2",
                  padx=4, pady=3,
                  command=lambda: self._sel_etq(None)
                  ).pack(side="left", padx=(6, 0))

        self._actualizar_btns_etq()

        # ── Fecha ──
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", pady=(12, 0))
        tk.Label(outer, text="Fecha y hora", bg=BG, fg=FG2,
                 font=("Segoe UI", 8, "bold"), anchor="w", padx=12
                 ).pack(fill="x", pady=(8, 4))

        fecha_row = tk.Frame(outer, bg=BG, padx=12)
        fecha_row.pack(fill="x")

        self.btn_fecha = tk.Button(
            fecha_row, text="＋ Cambiar fecha", bg=SURF, fg=FG2,
            relief="flat", font=("Segoe UI", 8), cursor="hand2",
            padx=8, pady=3,
            command=self._abrir_picker
        )
        self.btn_fecha.pack(side="left")

        self.chip_f = tk.Frame(fecha_row, bg=BG)
        self.lbl_chip_f = tk.Label(self.chip_f, text="", bg="#ebe9f8",
                                   fg=ACCENT, font=("Segoe UI", 7, "bold"),
                                   padx=6, pady=2)
        self.lbl_chip_f.pack(side="left")
        tk.Button(self.chip_f, text="×", bg="#ebe9f8", fg=ACCENT,
                  relief="flat", font=("Segoe UI", 8), cursor="hand2",
                  borderwidth=0, activebackground="#ebe9f8",
                  command=self._quitar_fecha
                  ).pack(side="left", padx=(0, 2))

        self._actualizar_chip_fecha()

        # ── Botones ──
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", pady=(12, 0))
        br = tk.Frame(outer, bg=BG, pady=10, padx=12)
        br.pack(fill="x")

        tk.Button(br, text="Cancelar", bg=BG, fg=FG3,
                  relief="flat", font=("Segoe UI", 9), cursor="hand2",
                  padx=10, pady=4, command=self.destroy
                  ).pack(side="left")
        tk.Button(br, text="Guardar cambios", bg=ACCENT, fg="#ffffff",
                  relief="flat", font=("Segoe UI", 9, "bold"), cursor="hand2",
                  padx=12, pady=4, command=self._guardar
                  ).pack(side="right")

    def _sel_etq(self, nombre):
        self._etiqueta = nombre
        self._actualizar_btns_etq()

    def _actualizar_btns_etq(self):
        for n, btn in self._btns_etq.items():
            if n == self._etiqueta:
                c = ETIQUETAS[n]
                btn.config(bg=c["bg"], fg=c["fg"])
            else:
                btn.config(bg=SURF, fg=FG3)

    def _abrir_picker(self):
        DateTimePicker(self, self._fecha_elegida, self._fecha)

    def _fecha_elegida(self, dt):
        self._fecha = dt
        self._actualizar_chip_fecha()

    def _quitar_fecha(self):
        self._fecha = None
        self._actualizar_chip_fecha()

    def _actualizar_chip_fecha(self):
        if self._fecha:
            self.lbl_chip_f.config(text=f"  {self._fecha.strftime('%d/%m/%Y  %H:%M')}  ")
            self.chip_f.pack(side="left", padx=(8, 0))
            self.btn_fecha.config(text="✎ Fecha", fg=ACCENT)
        else:
            self.chip_f.pack_forget()
            self.btn_fecha.config(text="＋ Cambiar fecha", fg=FG2)

    def _guardar(self):
        self.callback(self._etiqueta, self._fecha)
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.wm_attributes("-topmost", True)
        self.overrideredirect(True)
        self.wm_attributes("-alpha", 0.98)
        self.geometry("370x480+80+80")
        self.configure(bg=BORDER)
        self.minsize(370, 240)

        self.tareas: list[Tarea] = []
        self._drag_x = self._drag_y = 0
        self._resize_x = self._resize_y = self._resize_w = self._resize_h = 0
        self._fecha_pendiente = None
        self._etiqueta_pendiente = None

        self._build_ui()
        self._cargar()
        self._render_tareas()
        self._tick()
        self._setup_icono()
        self._iniciar_tray()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(fill="both", expand=True, padx=1, pady=1)

        # ── Header ──
        self.titlebar = tk.Frame(self.main, bg=HDR, height=46)
        self.titlebar.pack(fill="x")
        self.titlebar.pack_propagate(False)

        tk.Label(self.titlebar, text="Mis tareas", bg=HDR, fg="#ffffff",
                 font=("Segoe UI", 12, "bold"), anchor="w", padx=14
                 ).pack(side="left", fill="y")

        for txt, cmd in [("×", self.destroy), ("—", self._minimizar)]:
            tk.Button(self.titlebar, text=txt, bg=HDR, fg="#c8c6f7",
                      relief="flat", font=("Segoe UI", 12), cursor="hand2",
                      activebackground=HDR, activeforeground="#ffffff",
                      width=3, borderwidth=0, command=cmd
                      ).pack(side="right")

        self.titlebar.bind("<ButtonPress-1>", self._drag_start)
        self.titlebar.bind("<B1-Motion>",     self._drag_move)
        for w in self.titlebar.winfo_children():
            if isinstance(w, tk.Label):
                w.bind("<ButtonPress-1>", self._drag_start)
                w.bind("<B1-Motion>",     self._drag_move)

        # ── Campo de entrada ──
        entry_wrap = tk.Frame(self.main, bg=BG, padx=12, pady=10)
        entry_wrap.pack(fill="x")

        entry_row = tk.Frame(entry_wrap, bg=BG,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=ACCENT)
        entry_row.pack(fill="x")

        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            entry_row, textvariable=self.entry_var,
            bg=BG, fg=FG, insertbackground=ACCENT,
            relief="flat", font=("Segoe UI", 10),
            highlightthickness=0
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(10, 4))
        self.entry.bind("<Return>", lambda e: self._agregar())
        self._placeholder()

        tk.Button(entry_row, text="Agregar", bg=ACCENT, fg="#ffffff",
                  relief="flat", font=("Segoe UI", 9, "bold"),
                  cursor="hand2", borderwidth=0, padx=10,
                  activebackground="#4a4eb5", activeforeground="#ffffff",
                  command=self._agregar
                  ).pack(side="right", padx=4, pady=4)

        # ── Opciones de tarea ──
        opts = tk.Frame(self.main, bg=SURF, padx=12, pady=6,
                        highlightthickness=1, highlightbackground=BORDER)
        opts.pack(fill="x")

        self.btn_cal = tk.Button(
            opts, text="＋ Fecha", bg=SURF, fg=FG2,
            relief="flat", font=("Segoe UI", 8), cursor="hand2",
            borderwidth=0, activebackground=SURF, activeforeground=ACCENT,
            command=self._abrir_picker
        )
        self.btn_cal.pack(side="left")

        # Chip de fecha
        self.chip_fecha = tk.Frame(opts, bg=SURF)
        self.lbl_chip_fecha = tk.Label(
            self.chip_fecha, text="", bg="#ebe9f8", fg=ACCENT,
            font=("Segoe UI", 7, "bold"), padx=6, pady=2
        )
        self.lbl_chip_fecha.pack(side="left")
        tk.Button(self.chip_fecha, text="×", bg="#ebe9f8", fg=ACCENT,
                  relief="flat", font=("Segoe UI", 8), cursor="hand2",
                  borderwidth=0, activebackground="#ebe9f8",
                  command=self._quitar_fecha
                  ).pack(side="left", padx=(0, 2))

        tk.Frame(opts, bg=BORDER, width=1).pack(side="left", fill="y", padx=8, pady=2)

        self._btns_etiqueta = {}
        for nombre, colores in ETIQUETAS.items():
            btn = tk.Button(opts, text=nombre,
                            bg=colores["bg"], fg=colores["fg"],
                            relief="flat", font=("Segoe UI", 7, "bold"),
                            cursor="hand2", padx=5, pady=2, borderwidth=0,
                            activebackground=colores["bg"],
                            activeforeground=colores["fg"],
                            command=lambda n=nombre: self._toggle_etiqueta(n))
            btn.pack(side="left", padx=2)
            self._btns_etiqueta[nombre] = btn

        # ── Lista scrollable ──
        tk.Frame(self.main, bg=BORDER, height=1).pack(fill="x")

        canvas_frame = tk.Frame(self.main, bg=BG)
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(canvas_frame, orient="vertical",
                          command=self.canvas.yview,
                          bg=SURF, troughcolor=SURF, width=5)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.lista_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.lista_frame, anchor="nw"
        )
        self.lista_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>",      self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>",     self._scroll)
        self.lista_frame.bind("<MouseWheel>", self._scroll)

        # ── Footer ──
        tk.Frame(self.main, bg=BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self.main, bg=SURF, pady=6, padx=12)
        footer.pack(fill="x")

        self.lbl_contador = tk.Label(footer, text="", bg=SURF, fg=FG3,
                                     font=("Segoe UI", 8))
        self.lbl_contador.pack(side="left")

        tk.Button(footer, text="Limpiar completadas", bg=SURF, fg=FG3,
                  relief="flat", font=("Segoe UI", 8), cursor="hand2",
                  borderwidth=0, activebackground=SURF, activeforeground=RED,
                  command=self._limpiar_hechas
                  ).pack(side="right")

        # Resize
        rz = tk.Label(self.main, text="◢", bg=SURF, fg=BORDER,
                      cursor="size_nw_se", font=("Segoe UI", 8))
        rz.place(relx=1.0, rely=1.0, anchor="se")
        rz.bind("<ButtonPress-1>", self._resize_start)
        rz.bind("<B1-Motion>",     self._resize_move)

    # ── Placeholder ──────────────────────────────────────────────────────────

    def _placeholder(self):
        self.entry.insert(0, "Agregar una tarea")
        self.entry.config(fg=FG3)
        self.entry.bind("<FocusIn>",  self._clear_ph)
        self.entry.bind("<FocusOut>", self._set_ph)

    def _clear_ph(self, _=None):
        if self.entry.get() == "Agregar una tarea":
            self.entry.delete(0, "end")
            self.entry.config(fg=FG)

    def _set_ph(self, _=None):
        if not self.entry.get():
            self.entry.insert(0, "Agregar una tarea")
            self.entry.config(fg=FG3)

    # ── Fecha ────────────────────────────────────────────────────────────────

    def _abrir_picker(self):
        DateTimePicker(self, self._fecha_elegida, self._fecha_pendiente)

    def _fecha_elegida(self, dt):
        self._fecha_pendiente = dt
        if dt:
            self.lbl_chip_fecha.config(text=f"  {dt.strftime('%d/%m  %H:%M')}  ")
            self.chip_fecha.pack(side="left", padx=(4, 0))
            self.btn_cal.config(text="✎ Fecha", fg=ACCENT)
        else:
            self._quitar_fecha()

    def _quitar_fecha(self):
        self._fecha_pendiente = None
        self.chip_fecha.pack_forget()
        self.btn_cal.config(text="＋ Fecha", fg=FG2)

    # ── Etiquetas ────────────────────────────────────────────────────────────

    def _toggle_etiqueta(self, nombre):
        self._etiqueta_pendiente = None if self._etiqueta_pendiente == nombre else nombre
        self._actualizar_btns_etiqueta()

    def _actualizar_btns_etiqueta(self):
        for n, btn in self._btns_etiqueta.items():
            c = ETIQUETAS[n]
            if self._etiqueta_pendiente is None or n == self._etiqueta_pendiente:
                btn.config(bg=c["bg"], fg=c["fg"],
                           font=("Segoe UI", 7, "bold"),
                           relief="flat" if n != self._etiqueta_pendiente else "solid")
            else:
                btn.config(bg=SURF, fg=FG3,
                           font=("Segoe UI", 7), relief="flat")

    def _reset_etiqueta(self):
        self._etiqueta_pendiente = None
        for nombre, btn in self._btns_etiqueta.items():
            c = ETIQUETAS[nombre]
            btn.config(bg=c["bg"], fg=c["fg"],
                       font=("Segoe UI", 7, "bold"), relief="flat")

    # ── Tareas ───────────────────────────────────────────────────────────────

    def _agregar(self):
        texto = self.entry_var.get().strip()
        if not texto or texto == "Agregar una tarea":
            return
        self.tareas.append(Tarea(texto,
                                 fecha=self._fecha_pendiente,
                                 etiqueta=self._etiqueta_pendiente))
        self.entry_var.set("")
        self.entry.config(fg=FG)
        self._quitar_fecha()
        self._reset_etiqueta()
        self._guardar()
        self._render_tareas()

    def _editar(self, idx):
        def aplicar(etiqueta, fecha):
            self.tareas[idx].etiqueta = etiqueta
            self.tareas[idx].fecha    = fecha
            self._guardar()
            self._render_tareas()
        EditPopup(self, self.tareas[idx], aplicar)

    def _toggle(self, idx):
        self.tareas[idx].hecha = not self.tareas[idx].hecha
        self._guardar()
        self._render_tareas()

    def _eliminar(self, idx):
        self.tareas.pop(idx)
        self._guardar()
        self._render_tareas()

    def _limpiar_hechas(self):
        self.tareas = [t for t in self.tareas if not t.hecha]
        self._guardar()
        self._render_tareas()

    def _render_tareas(self):
        for w in self.lista_frame.winfo_children():
            w.destroy()
        for i, t in enumerate(self.tareas):
            self._row(i, t)
        total  = len(self.tareas)
        hechas = sum(1 for t in self.tareas if t.hecha)
        self.lbl_contador.config(
            text=f"{hechas} de {total} completadas" if total else "Sin tareas"
        )

    def _row(self, idx, tarea: Tarea):
        ahora   = datetime.now()
        vencida = tarea.fecha and tarea.fecha < ahora and not tarea.hecha
        proxima = (tarea.fecha and not vencida and not tarea.hecha and
                   (tarea.fecha - ahora).total_seconds() < 3600)

        fg   = FG3 if tarea.hecha else FG
        rbg  = "#f0f8fd" if tarea.hecha else "#ffffff"

        row = tk.Frame(self.lista_frame, bg=rbg,
                       highlightthickness=1,
                       highlightbackground=BORDER)
        row.pack(fill="x", pady=1, padx=0)

        # Franja de estado fecha
        if vencida:
            tk.Frame(row, bg=RED, width=3).pack(side="left", fill="y")
        elif proxima:
            tk.Frame(row, bg=ORANGE, width=3).pack(side="left", fill="y")
        elif tarea.fecha and not tarea.hecha:
            tk.Frame(row, bg=ACCENT, width=3).pack(side="left", fill="y")
        else:
            tk.Frame(row, bg=BG, width=3).pack(side="left", fill="y")

        inner = tk.Frame(row, bg=rbg, pady=9, padx=10)
        inner.pack(side="left", fill="x", expand=True)

        # Fila texto + etiqueta
        f1 = tk.Frame(inner, bg=rbg)
        f1.pack(fill="x")

        # Checkbox circular estilo MS To Do
        chk_txt = "✓" if tarea.hecha else "○"
        chk_fg  = ACCENT if tarea.hecha else BORDER
        chk = tk.Label(f1, text=chk_txt, bg=rbg,
                       fg=chk_fg, font=("Segoe UI", 13), cursor="hand2")
        chk.pack(side="left", padx=(0, 10))
        chk.bind("<Button-1>", lambda e, i=idx: self._toggle(i))

        lbl = tk.Label(f1, text=tarea.texto, bg=rbg, fg=fg,
                       font=("Segoe UI", 10,
                             "overstrike" if tarea.hecha else "normal"),
                       anchor="w", wraplength=155, justify="left",
                       cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True)
        lbl.bind("<Button-1>", lambda e, i=idx: self._toggle(i))

        if tarea.etiqueta and not tarea.hecha:
            c = ETIQUETAS.get(tarea.etiqueta, {})
            tk.Label(f1, text=tarea.etiqueta,
                     bg=c.get("bg", SURF), fg=c.get("fg", FG2),
                     font=("Segoe UI", 7, "bold"), padx=6, pady=2
                     ).pack(side="right", padx=(4, 0))

        # Fecha
        if tarea.fecha:
            fecha_str = tarea.fecha.strftime("%d %b  %H:%M")
            fecha_fg  = RED if vencida else ORANGE if proxima else (FG3 if tarea.hecha else FG2)
            prefijo   = "⚠  " if vencida else ("⏳  " if proxima else "⏰  ")
            tk.Label(inner, text=prefijo + fecha_str, bg=rbg, fg=fecha_fg,
                     font=("Segoe UI", 8), anchor="w", padx=23
                     ).pack(fill="x", pady=(2, 0))

        # Botones acción
        tk.Button(row, text="×", bg=rbg, fg=FG3,
                  relief="flat", font=("Segoe UI", 12), cursor="hand2",
                  borderwidth=0, activebackground=rbg, activeforeground=RED,
                  command=lambda i=idx: self._eliminar(i)
                  ).pack(side="right", padx=(0, 6))

        pencil = tk.Canvas(row, width=8, height=11, bg=rbg,
                           highlightthickness=0, cursor="hand2")
        pencil.create_rectangle(1, 0,  7, 2, fill="#f48fb1", outline="#f06292")
        pencil.create_rectangle(1, 2,  7, 4, fill="#b3e5fc", outline="#81d4fa")
        pencil.create_rectangle(1, 4,  7, 8, fill="#fdd835", outline="#f9a825")
        pencil.create_polygon(1, 8, 7, 8, 4, 11,  fill="#9e9e9e", outline="#757575")
        pencil.bind("<Button-1>", lambda e, i=idx: self._editar(i))
        pencil.pack(side="right", padx=(0, 6), pady=7)

        for w in [row, inner, f1, lbl]:
            w.bind("<MouseWheel>", self._scroll)

    # ── Tick ─────────────────────────────────────────────────────────────────

    def _tick(self):
        self._render_tareas()
        self.after(60_000, self._tick)

    # ── Persistencia ─────────────────────────────────────────────────────────

    def _guardar(self):
        data = [{"texto": t.texto, "hecha": t.hecha,
                 "fecha": t.fecha.isoformat() if t.fecha else None,
                 "etiqueta": t.etiqueta} for t in self.tareas]
        with open(ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _cargar(self):
        if not os.path.exists(ARCHIVO):
            return
        try:
            with open(ARCHIVO, encoding="utf-8") as f:
                data = json.load(f)
            self.tareas = [
                Tarea(d["texto"], d["hecha"],
                      datetime.fromisoformat(d["fecha"]) if d.get("fecha") else None,
                      d.get("etiqueta"))
                for d in data
            ]
        except Exception:
            self.tareas = []

    # ── Arrastrar ────────────────────────────────────────────────────────────

    def _drag_start(self, e):
        self._drag_x = e.x_root - self.winfo_x()
        self._drag_y = e.y_root - self.winfo_y()

    def _drag_move(self, e):
        self.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ── Redimensionar ─────────────────────────────────────────────────────────

    def _resize_start(self, e):
        self._resize_x, self._resize_y = e.x_root, e.y_root
        self._resize_w, self._resize_h = self.winfo_width(), self.winfo_height()

    def _resize_move(self, e):
        nw = max(240, self._resize_w + (e.x_root - self._resize_x))
        nh = max(240, self._resize_h + (e.y_root - self._resize_y))
        self.geometry(f"{nw}x{nh}")

    # ── Ícono y bandeja ──────────────────────────────────────────────────────

    def _setup_icono(self):
        """Asigna el ícono a la ventana."""
        if os.path.exists(ICON_PATH):
            try:
                self.iconbitmap(ICON_PATH)
            except Exception:
                pass

    def _crear_imagen_tray(self):
        """Genera la imagen del ícono para la bandeja."""
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([2, 2, 62, 62], fill="#5b5fc7")
        d.rounded_rectangle([16, 18, 48, 52], radius=4, fill="white")
        d.rounded_rectangle([24, 14, 40, 22], radius=3, fill="#5b5fc7")
        d.rounded_rectangle([26, 16, 38, 20], radius=2, fill="white")
        for y in [28, 35, 42]:
            d.ellipse([20, y-3, 26, y+3], outline="white", width=2)
            d.rounded_rectangle([29, y-2, 44, y+2], radius=1, fill="white")
        return img

    def _iniciar_tray(self):
        """Crea el ícono en la bandeja del sistema."""
        menu = pystray.Menu(
            pystray.MenuItem("Mostrar", self._mostrar_desde_tray, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Cerrar", self._cerrar_desde_tray),
        )
        self._tray_icon = pystray.Icon(
            "MisTareas",
            self._crear_imagen_tray(),
            "Mis Tareas",
            menu
        )
        t = threading.Thread(target=self._tray_icon.run, daemon=True)
        t.start()

    def _mostrar_desde_tray(self):
        self.after(0, self._restaurar_ventana)

    def _cerrar_desde_tray(self):
        self._tray_icon.stop()
        self.after(0, self.destroy)

    def _restaurar_ventana(self):
        self.overrideredirect(True)
        self.deiconify()
        self.wm_attributes("-topmost", True)
        self.lift()

    # ── Minimizar ─────────────────────────────────────────────────────────────

    def _minimizar(self):
        """Oculta la ventana a la bandeja del sistema."""
        self.overrideredirect(False)
        self.withdraw()

    def _restaurar(self, _=None):
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.unbind("<Map>")

    # ── Scroll ───────────────────────────────────────────────────────────────

    def _scroll(self, e):
        self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _on_frame_configure(self, _=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, e):
        self.canvas.itemconfig(self.canvas_window, width=e.width)


if __name__ == "__main__":
    App().mainloop()
