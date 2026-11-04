"""Piezas compartidas por las pantallas."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from smartclothes.modelo.errores import PersistenciaError, ReglaNegocioError

MODULOS = (
    ("inicio", "Inicio"),
    ("productos", "Productos"),
    ("tiendas", "Tiendas"),
    ("traslados", "Órdenes de traslado"),
    ("mermas", "Mermas y pérdidas"),
    ("comprobantes", "Comprobantes"),
)

FONDO = "#f3f0ec"
ACENTO = "#d9cbb8"


def informar(parent: tk.Misc, titulo: str, mensaje: str) -> None:
    messagebox.showinfo(titulo, mensaje, parent=parent)


def mostrar_error(parent: tk.Misc, mensaje: str) -> None:
    messagebox.showerror("No se pudo completar", mensaje, parent=parent)


def pedir_confirmacion(parent: tk.Misc, titulo: str, mensaje: str) -> bool:
    return bool(messagebox.askyesno(titulo, mensaje, parent=parent))


def titulo(parent: tk.Misc, texto: str) -> ttk.Label:
    etiqueta = ttk.Label(parent, text=texto, style="Titulo.TLabel")
    etiqueta.pack(anchor="w", pady=(0, 12))
    return etiqueta


NUMERICAS = {"stock", "disponible", "cantidad", "unidades"}


def crear_tabla(
    parent: tk.Misc,
    columnas: tuple[str, ...],
    encabezados: tuple[str, ...],
    anchos: tuple[int, ...],
    altura: int = 8,
    con_imagen: bool = False,
) -> tuple[ttk.Frame, ttk.Treeview]:
    """Tabla con scroll. Con con_imagen=True la primera columna muestra la foto."""
    marco = ttk.Frame(parent)
    estilo = "Fotos.Treeview" if con_imagen else "Treeview"
    tabla = ttk.Treeview(
        marco,
        columns=columnas,
        show="tree headings" if con_imagen else "headings",
        height=altura,
        selectmode="browse",
        style=estilo,
    )
    if con_imagen:
        tabla.heading("#0", text="Foto")
        tabla.column("#0", width=70, stretch=False, anchor="center")
    scroll = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    for columna, encabezado, ancho in zip(columnas, encabezados, anchos):
        tabla.heading(columna, text=encabezado)
        tabla.column(columna, width=ancho, anchor="e" if columna in NUMERICAS else "w")
    tabla.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    marco.rowconfigure(0, weight=1)
    marco.columnconfigure(0, weight=1)
    return marco, tabla


def configurar_combo(combo: ttk.Combobox, etiquetas: list[str], actual: str) -> None:
    combo["values"] = etiquetas
    if actual in etiquetas:
        combo.set(actual)
    elif etiquetas:
        combo.current(0)
    else:
        combo.set("")


def cargar_miniatura(ruta: Path | None, lado: int) -> tk.PhotoImage | None:
    """Carga PNG o GIF y la reduce para que quepa en un cuadrado de `lado` píxeles."""
    if ruta is None:
        return None
    try:
        imagen = tk.PhotoImage(file=str(ruta))
    except tk.TclError:
        return None
    factor = max(1, -(-max(imagen.width(), imagen.height()) // lado))
    return imagen.subsample(factor, factor) if factor > 1 else imagen


class Pantalla(ttk.Frame):
    """Las pantallas llaman al controlador. Las reglas viven en el modelo."""

    def __init__(self, master: tk.Misc, controlador):
        super().__init__(master, padding=16)
        self.controlador = controlador

    def refrescar(self) -> None:
        return None

    def ejecutar(self, accion):
        try:
            return True, accion()
        except (ReglaNegocioError, PersistenciaError) as error:
            mostrar_error(self.winfo_toplevel(), str(error))
            return False, None


__all__ = [
    "ACENTO",
    "FONDO",
    "MODULOS",
    "Pantalla",
    "cargar_miniatura",
    "configurar_combo",
    "crear_tabla",
    "informar",
    "mostrar_error",
    "pedir_confirmacion",
    "titulo",
]
