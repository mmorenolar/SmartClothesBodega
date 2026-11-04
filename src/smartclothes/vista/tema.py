"""Aspecto visual de toda la aplicación.

Para cambiar colores, tamaños de letra o el estilo de los botones,
basta con editar este archivo: las pantallas solo usan estos nombres.
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# ----- Paleta de colores -----
COLORES = {
    "fondo": "#f4f5f7",          # fondo general de la ventana
    "tarjeta": "#ffffff",        # fondo de las tarjetas blancas
    "borde": "#e3e6eb",          # líneas finas alrededor de tarjetas y campos
    "texto": "#1f2430",          # texto principal
    "suave": "#6b7280",          # texto secundario (gris)
    "lateral": "#1d2433",        # menú lateral oscuro
    "lateral_hover": "#2a3346",  # menú lateral al pasar el mouse
    "lateral_texto": "#aeb6c6",  # texto del menú lateral
    "acento": "#2f6fed",         # color principal de la marca (botones, selección)
    "acento_hover": "#2259c9",
    "acento_suave": "#e8f0fe",
    "exito": "#1a7f45",
    "exito_suave": "#e3f5ea",
    "peligro": "#c0392b",
    "peligro_suave": "#fdecea",
    "aviso": "#a85f00",
    "aviso_suave": "#fff3dd",
    "zebra": "#f8f9fb",          # filas alternadas de las tablas
}

# ----- Tipografía -----
FUENTES_PREFERIDAS = ("Segoe UI", "Inter", "Helvetica Neue", "Helvetica", "Arial")
MONO_PREFERIDAS = ("Consolas", "Cascadia Mono", "DejaVu Sans Mono", "Courier New", "Courier")

FUENTE = "TkDefaultFont"
MONO = "TkFixedFont"


def fuente(tamano: int = 10, peso: str = "normal") -> tuple:
    return (FUENTE, tamano, peso)


def mono(tamano: int = 10, peso: str = "normal") -> tuple:
    return (MONO, tamano, peso)


def _elegir(raiz: tk.Misc, preferidas: tuple[str, ...], respaldo: str) -> str:
    disponibles = set(tkfont.families(raiz))
    return next((nombre for nombre in preferidas if nombre in disponibles), respaldo)


def aplicar(raiz: tk.Tk) -> None:
    """Configura fuentes y estilos ttk. Se llama una vez al abrir la ventana."""
    global FUENTE, MONO
    FUENTE = _elegir(raiz, FUENTES_PREFERIDAS, "TkDefaultFont")
    MONO = _elegir(raiz, MONO_PREFERIDAS, "TkFixedFont")
    c = COLORES

    raiz.configure(background=c["fondo"])
    # Fuente de los widgets clásicos de tk y de los campos ttk (los textos ttk usan sus estilos).
    for clase in ("Label", "Button", "Text", "Listbox", "Menu", "TEntry", "TCombobox", "TSpinbox"):
        raiz.option_add(f"*{clase}.font", fuente(10))
    raiz.option_add("*TCombobox*Listbox.font", fuente(10))
    raiz.option_add("*TCombobox*Listbox.selectBackground", c["acento"])

    estilo = ttk.Style(raiz)
    if "clam" in estilo.theme_names():
        estilo.theme_use("clam")

    estilo.configure(".", background=c["fondo"], foreground=c["texto"], font=fuente(10),
                     bordercolor=c["borde"], focuscolor=c["acento"])
    estilo.configure("TFrame", background=c["fondo"])
    estilo.configure("Tarjeta.TFrame", background=c["tarjeta"])

    # Textos
    estilo.configure("TLabel", background=c["fondo"], foreground=c["texto"])
    estilo.configure("Titulo.TLabel", font=fuente(20, "bold"))
    estilo.configure("Subtitulo.TLabel", foreground=c["suave"], font=fuente(10))
    estilo.configure("Tarjeta.TLabel", background=c["tarjeta"])
    estilo.configure("Seccion.TLabel", background=c["tarjeta"], font=fuente(12, "bold"))
    estilo.configure("Campo.TLabel", background=c["tarjeta"], foreground=c["suave"], font=fuente(9))
    estilo.configure("Ayuda.TLabel", background=c["tarjeta"], foreground=c["suave"], font=fuente(9))
    estilo.configure("Grande.TLabel", background=c["tarjeta"], font=fuente(16, "bold"))

    # Botones
    estilo.configure("TButton", background=c["tarjeta"], foreground=c["texto"], padding=(14, 7),
                     borderwidth=1, relief="solid", bordercolor="#d3d8e0", lightcolor=c["tarjeta"],
                     darkcolor=c["tarjeta"], font=fuente(10), width=-6)
    estilo.map("TButton",
               background=[("disabled", c["tarjeta"]), ("pressed", "#e9ecf1"), ("active", "#f0f2f5")],
               foreground=[("disabled", "#b4bac4")],
               bordercolor=[("focus", c["acento"])])
    estilo.configure("Primario.TButton", background=c["acento"], foreground="#ffffff", bordercolor=c["acento"],
                     lightcolor=c["acento"], darkcolor=c["acento"], font=fuente(10, "bold"))
    estilo.map("Primario.TButton",
               background=[("disabled", "#a9c1f5"), ("pressed", c["acento_hover"]), ("active", c["acento_hover"])],
               foreground=[("disabled", "#ffffff")],
               bordercolor=[("disabled", "#a9c1f5"), ("active", c["acento_hover"])])
    estilo.configure("Peligro.TButton", background=c["tarjeta"], foreground=c["peligro"], bordercolor="#f0c4be")
    estilo.map("Peligro.TButton",
               background=[("disabled", c["tarjeta"]), ("active", c["peligro_suave"])],
               foreground=[("disabled", "#e3b3ad")])
    estilo.configure("Enlace.TButton", background=c["tarjeta"], foreground=c["acento"], borderwidth=0,
                     relief="flat",
                     padding=(4, 2), font=fuente(9, "bold"))
    estilo.map("Enlace.TButton", background=[("active", c["acento_suave"])],
               foreground=[("disabled", "#b4bac4")])

    # Botones de opción tipo "segmento" (Pantalón | Calzado | Polera)
    estilo.configure("Segmento.Toolbutton", background=c["tarjeta"], foreground=c["texto"],
                     padding=(12, 6), borderwidth=1, relief="flat", anchor="center")
    estilo.map("Segmento.Toolbutton",
               background=[("selected", c["acento"]), ("disabled", "#f3f4f6"), ("active", "#f0f2f5")],
               foreground=[("selected", "#ffffff"), ("disabled", "#b4bac4")],
               bordercolor=[("selected", c["acento"])])

    # Campos de texto y listas desplegables
    for clase in ("TEntry", "TCombobox", "TSpinbox"):
        estilo.configure(clase, fieldbackground=c["tarjeta"], background=c["tarjeta"], bordercolor=c["borde"],
                         lightcolor=c["borde"], darkcolor=c["borde"], padding=(8, 5), arrowcolor=c["suave"])
        estilo.map(clase,
                   bordercolor=[("focus", c["acento"])],
                   lightcolor=[("focus", c["acento"])],
                   fieldbackground=[("disabled", "#f3f4f6"), ("readonly", c["tarjeta"])],
                   foreground=[("disabled", "#8a919c")])
    estilo.configure("TCheckbutton", background=c["tarjeta"])

    # Tablas
    estilo.configure("Treeview", background=c["tarjeta"], fieldbackground=c["tarjeta"], foreground=c["texto"],
                     rowheight=30, borderwidth=0, font=fuente(10))
    estilo.map("Treeview", background=[("selected", c["acento_suave"])], foreground=[("selected", c["texto"])])
    estilo.configure("Treeview.Heading", background=c["tarjeta"], foreground=c["suave"], relief="flat",
                     font=fuente(9, "bold"), padding=(6, 8), borderwidth=0)
    estilo.map("Treeview.Heading", background=[("active", c["zebra"])])
    estilo.configure("Fotos.Treeview", rowheight=56)
    estilo.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    estilo.layout("Fotos.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])

    estilo.configure("Vertical.TScrollbar", background=c["fondo"], troughcolor=c["tarjeta"], borderwidth=0,
                     arrowcolor=c["suave"], gripcount=0)
    estilo.configure("Ocupacion.Horizontal.TProgressbar", troughcolor="#eceff3", background=c["acento"],
                     bordercolor="#eceff3", lightcolor=c["acento"], darkcolor=c["acento"], thickness=8)
    estilo.configure("TSeparator", background=c["borde"])
