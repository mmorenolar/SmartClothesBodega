"""Piezas compartidas por las pantallas: tarjetas, chips, tablas, avisos y animaciones."""

import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk

from smartclothes.modelo.errores import PersistenciaError, ReglaNegocioError
from smartclothes.vista import tema
from smartclothes.vista.tema import COLORES

# clave, texto del menú, ícono, subtítulo de la pantalla
MODULOS = (
    ("inicio", "Inicio", "⌂", "Resumen de la bodega principal"),
    ("productos", "Productos", "▦", "Prendas en bodega, fotos y stock"),
    ("tiendas", "Tiendas", "⚑", "Tiendas que reciben los traslados"),
    ("traslados", "Órdenes de traslado", "⇄", "Envía prendas a una tienda en tres pasos"),
    ("mermas", "Mermas y pérdidas", "⚠", "Bajas por daño, pérdida o falla de fábrica"),
    ("comprobantes", "Comprobantes", "≡", "Documentos emitidos con su folio"),
)

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre")


def fecha_larga(fecha: date) -> str:
    return f"{DIAS[fecha.weekday()].capitalize()} {fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


# ----- Avisos (toast): aparecen en la esquina y se van solos -----

_ESTILO_AVISO = {
    "exito": ("✓", "exito"),
    "error": ("✕", "peligro"),
    "info": ("i", "acento"),
}


def notificar(parent: tk.Misc, titulo: str, mensaje: str, tipo: str = "exito", duracion: int = 3200) -> None:
    """Muestra un aviso que entra deslizándose por la derecha y desaparece solo."""
    try:
        raiz = parent.winfo_toplevel()
    except tk.TclError:
        return
    icono, clave = _ESTILO_AVISO.get(tipo, _ESTILO_AVISO["info"])
    color = COLORES[clave]
    caja = tk.Frame(raiz, bg=COLORES["tarjeta"], highlightthickness=1, highlightbackground=COLORES["borde"])
    tk.Frame(caja, bg=color, width=5).pack(side="left", fill="y")
    cuerpo = tk.Frame(caja, bg=COLORES["tarjeta"], padx=14, pady=10)
    cuerpo.pack(side="left", fill="both")
    tk.Label(cuerpo, text=f"{icono}  {titulo}", bg=COLORES["tarjeta"], fg=color,
             font=tema.fuente(10, "bold")).pack(anchor="w")
    tk.Label(cuerpo, text=mensaje, bg=COLORES["tarjeta"], fg=COLORES["texto"], wraplength=300,
             justify="left", font=tema.fuente(9)).pack(anchor="w", pady=(2, 0))
    caja.bind("<Button-1>", lambda _e: _cerrar_aviso(raiz, caja))

    pila = getattr(raiz, "_avisos", [])
    raiz._avisos = pila
    pila.append(caja)
    _ubicar_avisos(raiz, animar=caja)
    raiz.after(duracion, lambda: _cerrar_aviso(raiz, caja))


def _ubicar_avisos(raiz, animar=None) -> None:
    margen = 20
    for caja in list(raiz._avisos):
        try:
            caja.update_idletasks()
            alto = caja.winfo_reqheight()
            if caja is animar:
                _deslizar(caja, margen, 340, -20)
            else:
                caja.place_configure(y=-margen)
            caja.lift()
        except tk.TclError:
            continue
        margen += alto + 10


def _deslizar(caja, y: int, desde: int, hasta: int, paso: int = 0, al_final=None) -> None:
    pasos = 10
    try:
        avance = 1 - (1 - paso / pasos) ** 3  # empieza rápido y frena suave
        x = int(desde + (hasta - desde) * avance)
        caja.place(relx=1.0, rely=1.0, x=x, y=-y, anchor="se")
        caja.lift()
    except tk.TclError:
        return
    if paso < pasos:
        caja.after(16, lambda: _deslizar(caja, y, desde, hasta, paso + 1, al_final))
    elif al_final:
        al_final()


def _cerrar_aviso(raiz, caja) -> None:
    if caja not in getattr(raiz, "_avisos", []):
        return
    raiz._avisos.remove(caja)

    def destruir():
        try:
            caja.destroy()
        except tk.TclError:
            pass
        _ubicar_avisos(raiz)

    try:
        y = -int(caja.place_info().get("y", -20))
    except (tk.TclError, ValueError):
        y = 20
    _deslizar(caja, y, -20, 360, al_final=destruir)


def informar(parent: tk.Misc, titulo: str, mensaje: str) -> None:
    notificar(parent, titulo, mensaje, "exito")


def mostrar_error(parent: tk.Misc, mensaje: str) -> None:
    notificar(parent, "No se pudo completar", mensaje, "error", duracion=5000)


def pedir_confirmacion(parent: tk.Misc, titulo: str, mensaje: str) -> bool:
    """Las acciones que no se pueden deshacer siguen pidiendo un sí explícito."""
    return bool(messagebox.askyesno(titulo, mensaje, parent=parent))


# ----- Bloques visuales -----

class Tarjeta(tk.Frame):
    """Caja blanca con borde fino. Base de casi todos los paneles."""

    def __init__(self, master, padding: int = 18, **opciones):
        super().__init__(master, bg=COLORES["tarjeta"], highlightthickness=1,
                         highlightbackground=COLORES["borde"], padx=padding, pady=padding - 2, **opciones)


def encabezado(pantalla: tk.Misc, titulo: str, subtitulo: str = "") -> ttk.Frame:
    """Título grande de la pantalla. Devuelve el marco para agregar botones a la derecha."""
    marco = ttk.Frame(pantalla)
    marco.pack(fill="x", pady=(0, 16))
    textos = ttk.Frame(marco)
    textos.pack(side="left")
    ttk.Label(textos, text=titulo, style="Titulo.TLabel").pack(anchor="w")
    if subtitulo:
        ttk.Label(textos, text=subtitulo, style="Subtitulo.TLabel").pack(anchor="w")
    return marco


def titulo(parent: tk.Misc, texto: str) -> ttk.Label:
    etiqueta = ttk.Label(parent, text=texto, style="Titulo.TLabel")
    etiqueta.pack(anchor="w", pady=(0, 12))
    return etiqueta


_CHIP = {
    "exito": ("exito", "exito_suave"),
    "peligro": ("peligro", "peligro_suave"),
    "aviso": ("aviso", "aviso_suave"),
    "acento": ("acento", "acento_suave"),
    "neutro": ("suave", "zebra"),
}


def chip(parent: tk.Misc, texto: str, tipo: str = "neutro") -> tk.Label:
    """Etiqueta pequeña de color, como las de estado en las apps."""
    etiqueta = tk.Label(parent, font=tema.fuente(9, "bold"), padx=8, pady=2)
    pintar_chip(etiqueta, texto, tipo)
    return etiqueta


def pintar_chip(etiqueta: tk.Label, texto: str, tipo: str) -> None:
    color, fondo = _CHIP.get(tipo, _CHIP["neutro"])
    etiqueta.configure(text=texto, fg=COLORES[color], bg=COLORES[fondo])


def chip_estado_producto(producto, umbral: int = 10) -> tuple[str, str]:
    if not producto.disponible:
        return "Agotado", "peligro"
    if producto.stock <= umbral:
        return "Stock bajo", "aviso"
    return "Disponible", "exito"


def etiqueta_campo(parent: tk.Misc, texto: str) -> ttk.Label:
    return ttk.Label(parent, text=texto, style="Campo.TLabel")


def separador(parent: tk.Misc, **pack) -> None:
    tk.Frame(parent, bg=COLORES["borde"], height=1).pack(fill="x", **(pack or {"pady": 12}))


def al_pasar(widgets, normal: str, encima: str) -> None:
    """Cambia el fondo de uno o varios widgets tk cuando el mouse pasa por encima."""
    lista = widgets if isinstance(widgets, (list, tuple)) else [widgets]

    def pintar(color):
        for widget in lista:
            try:
                widget.configure(bg=color)
            except tk.TclError:
                pass

    for widget in lista:
        widget.bind("<Enter>", lambda _e: pintar(encima), add="+")
        widget.bind("<Leave>", lambda _e: pintar(normal), add="+")


def animar_numero(etiqueta: tk.Label | ttk.Label, destino: int, formato=str, duracion: int = 600) -> None:
    """Hace que un número suba contando desde 0 hasta su valor."""
    pasos = max(1, duracion // 20)
    trabajo = getattr(etiqueta, "_animacion", None)
    if trabajo:
        try:
            etiqueta.after_cancel(trabajo)
        except tk.TclError:
            pass

    def paso(n: int) -> None:
        avance = 1 - (1 - n / pasos) ** 3
        try:
            etiqueta.configure(text=formato(round(destino * avance)))
            if n < pasos:
                etiqueta._animacion = etiqueta.after(20, lambda: paso(n + 1))
            else:
                etiqueta._animacion = None
        except tk.TclError:
            pass

    paso(0)


# ----- Tablas -----

NUMERICAS = {"stock", "disponible", "cantidad", "unidades", "ordenes"}


def crear_tabla(
    parent: tk.Misc,
    columnas: tuple[str, ...],
    encabezados: tuple[str, ...],
    anchos: tuple[int, ...],
    altura: int = 8,
    con_imagen: bool = False,
) -> tuple[tk.Frame, ttk.Treeview]:
    """Tabla con scroll y filas alternadas. Con con_imagen=True la primera columna muestra la foto."""
    marco = tk.Frame(parent, bg=COLORES["tarjeta"])
    tabla = ttk.Treeview(
        marco,
        columns=columnas,
        show="tree headings" if con_imagen else "headings",
        height=altura,
        selectmode="browse",
        style="Fotos.Treeview" if con_imagen else "Treeview",
    )
    if con_imagen:
        tabla.heading("#0", text="")
        tabla.column("#0", width=66, stretch=False, anchor="center")
    scroll = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=scroll.set)
    for columna, encabezado_col, ancho in zip(columnas, encabezados, anchos):
        alineacion = "e" if columna in NUMERICAS else "w"
        tabla.heading(columna, text=encabezado_col.upper(), anchor=alineacion)
        tabla.column(columna, width=ancho, minwidth=40, anchor=alineacion)
    tabla.tag_configure("par", background=COLORES["tarjeta"])
    tabla.tag_configure("impar", background=COLORES["zebra"])
    tabla.tag_configure("peligro", foreground=COLORES["peligro"])
    tabla.tag_configure("aviso", foreground=COLORES["aviso"])
    tabla.tag_configure("exito", foreground=COLORES["exito"])
    tabla.tag_configure("suave", foreground=COLORES["suave"])
    tabla.grid(row=0, column=0, sticky="nsew")
    scroll.grid(row=0, column=1, sticky="ns")
    marco.rowconfigure(0, weight=1)
    marco.columnconfigure(0, weight=1)
    return marco, tabla


def fila(tabla: ttk.Treeview, iid: str, valores: tuple, tags: tuple = (), **opciones) -> None:
    """Inserta una fila alternando el color de fondo."""
    franja = "impar" if len(tabla.get_children()) % 2 else "par"
    tabla.insert("", "end", iid=iid, values=valores, tags=(franja, *tags), **opciones)


def vacio(tabla: ttk.Treeview, texto: str) -> None:
    tabla.insert("", "end", iid="__vacio__", values=(texto,), tags=("suave",))


def configurar_combo(combo: ttk.Combobox, etiquetas: list[str], actual: str) -> None:
    combo["values"] = etiquetas
    if actual in etiquetas:
        combo.set(actual)
    elif etiquetas:
        combo.current(0)
    else:
        combo.set("")


class ComboBuscador(ttk.Combobox):
    """Lista desplegable que filtra sus opciones a medida que se escribe."""

    def __init__(self, master, **opciones):
        super().__init__(master, **opciones)
        self._opciones: list[str] = []
        self.bind("<KeyRelease>", self._filtrar, add="+")

    def opciones(self, valores: list[str]) -> None:
        self._opciones = list(valores)
        self["values"] = self._opciones

    def _filtrar(self, evento=None) -> None:
        if evento is not None and evento.keysym in {"Up", "Down", "Return", "Escape", "Tab"}:
            return
        texto = self.get().strip().lower()
        self["values"] = [valor for valor in self._opciones if texto in valor.lower()] or self._opciones


def cargar_miniatura(ruta: Path | None, lado: int):
    """Carga la foto y la reduce para que quepa en un cuadrado de `lado` píxeles.

    Con Pillow instalado acepta JPG y achica con mejor calidad; si no, usa PNG o GIF.
    """
    if ruta is None:
        return None
    try:
        from PIL import Image, ImageTk

        with Image.open(ruta) as imagen:
            imagen = imagen.copy()
        imagen.thumbnail((lado, lado), Image.LANCZOS)
        return ImageTk.PhotoImage(imagen)
    except ImportError:
        pass
    except (OSError, tk.TclError):
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
        super().__init__(master, padding=(28, 22, 28, 22))
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
    "COLORES",
    "MODULOS",
    "ComboBuscador",
    "Pantalla",
    "Tarjeta",
    "al_pasar",
    "animar_numero",
    "cargar_miniatura",
    "chip",
    "chip_estado_producto",
    "configurar_combo",
    "crear_tabla",
    "encabezado",
    "etiqueta_campo",
    "fecha_larga",
    "fila",
    "informar",
    "mostrar_error",
    "notificar",
    "pedir_confirmacion",
    "pintar_chip",
    "separador",
    "titulo",
    "vacio",
]
