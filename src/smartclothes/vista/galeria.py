"""Galería de tarjetas con foto, nombre y SKU (vista tipo tienda).

Ofrece los mismos métodos que usa la pantalla con una tabla ttk.Treeview
(get_children, selection, selection_set, exists, see, delete), así la
pantalla de Productos casi no cambia.
"""

import tkinter as tk

from smartclothes.vista import tema
from smartclothes.vista.comun import COLORES, pintar_chip

ANCHO_TARJETA = 138
ALTO_TARJETA = 220
SEPARACION = 10
LADO_FOTO = 104


class TarjetaProducto(tk.Frame):
    """Una prenda: foto grande, nombre, SKU y etiqueta de estado."""

    def __init__(self, master, sku: str, imagen, nombre: str, estado: str, tipo_estado: str, al_elegir):
        super().__init__(master, bg=COLORES["tarjeta"], width=ANCHO_TARJETA, height=ALTO_TARJETA,
                         highlightthickness=2, highlightbackground=COLORES["borde"], cursor="hand2")
        self.pack_propagate(False)
        self.sku = sku
        self._elegida = False
        caja = tk.Frame(self, bg=COLORES["tarjeta"], width=LADO_FOTO + 16, height=LADO_FOTO + 8)
        caja.pack(pady=(8, 4))
        caja.pack_propagate(False)
        self._foto = tk.Label(caja, bg=COLORES["tarjeta"], fg=COLORES["suave"])
        if imagen is not None:
            self._foto.configure(image=imagen)
            self._foto.image = imagen  # Tkinter necesita guardar la referencia para mostrarla
        else:
            self._foto.configure(text="Sin foto")
        self._foto.pack(expand=True)
        self._nombre = tk.Label(self, text=nombre, bg=COLORES["tarjeta"], font=tema.fuente(10, "bold"),
                                wraplength=ANCHO_TARJETA - 16, justify="center")
        self._nombre.pack(padx=8)
        self._sku = tk.Label(self, text=sku, bg=COLORES["tarjeta"], fg=COLORES["suave"], font=tema.fuente(8))
        self._sku.pack()
        self._chip = tk.Label(self, font=tema.fuente(8, "bold"), padx=6, pady=1)
        pintar_chip(self._chip, estado, tipo_estado)
        self._chip.pack(pady=(4, 0))
        for widget in (self, caja, self._foto, self._nombre, self._sku, self._chip):
            widget.bind("<Button-1>", lambda _e: al_elegir(self.sku))
            widget.bind("<Enter>", lambda _e: self._pintar(encima=True), add="+")
            widget.bind("<Leave>", lambda _e: self._pintar(encima=False), add="+")

    def marcar(self, elegida: bool) -> None:
        self._elegida = elegida
        self._pintar(encima=False)

    def _pintar(self, encima: bool) -> None:
        if self._elegida:
            color = COLORES["acento"]
        else:
            color = "#c9d3e3" if encima else COLORES["borde"]
        self.configure(highlightbackground=color, highlightcolor=color)


class Galeria(tk.Frame):
    """Cuadrícula con scroll que reacomoda las columnas según el ancho disponible."""

    def __init__(self, master):
        super().__init__(master, bg=COLORES["tarjeta"])
        self._lienzo = tk.Canvas(self, bg=COLORES["tarjeta"], highlightthickness=0)
        self._barra = tk.Scrollbar(self, orient="vertical", command=self._lienzo.yview)
        self._lienzo.configure(yscrollcommand=self._barra.set)
        self._lienzo.grid(row=0, column=0, sticky="nsew")
        self._barra.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._interior = tk.Frame(self._lienzo, bg=COLORES["tarjeta"])
        self._ventana = self._lienzo.create_window((0, 0), window=self._interior, anchor="nw")
        self._tarjetas: dict[str, TarjetaProducto] = {}
        self._orden: list[str] = []
        self._seleccion: str | None = None
        self._columnas = 0
        self._lienzo.bind("<Configure>", lambda _e: self._acomodar())
        self._interior.bind("<Configure>", lambda _e: self._lienzo.configure(scrollregion=self._lienzo.bbox("all")))
        self._lienzo.bind("<Enter>", lambda _e: self._activar_rueda(True))
        self._lienzo.bind("<Leave>", lambda _e: self._activar_rueda(False))

    # ----- Rueda del mouse -----

    def _activar_rueda(self, activa: bool) -> None:
        if activa:
            self._lienzo.bind_all("<MouseWheel>", lambda e: self._lienzo.yview_scroll(-e.delta // 120, "units"))
            self._lienzo.bind_all("<Button-4>", lambda _e: self._lienzo.yview_scroll(-1, "units"))
            self._lienzo.bind_all("<Button-5>", lambda _e: self._lienzo.yview_scroll(1, "units"))
        else:
            for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                self._lienzo.unbind_all(evento)

    # ----- Contenido -----

    def agregar(self, sku: str, imagen, nombre: str, estado: str, tipo_estado: str) -> None:
        tarjeta = TarjetaProducto(self._interior, sku, imagen, nombre, estado, tipo_estado, self.selection_set)
        tarjeta.marcar(sku == self._seleccion)
        self._tarjetas[sku] = tarjeta
        self._orden.append(sku)
        self._columnas = 0
        self._acomodar()

    def _acomodar(self) -> None:
        ancho = max(self._lienzo.winfo_width(), ANCHO_TARJETA + SEPARACION)
        columnas = max(1, (ancho - SEPARACION) // (ANCHO_TARJETA + SEPARACION))
        if columnas != self._columnas:
            self._columnas = columnas
            for indice, sku in enumerate(self._orden):
                self._tarjetas[sku].grid(row=indice // columnas, column=indice % columnas,
                                         padx=(SEPARACION, 0), pady=(SEPARACION, 0))
        self._lienzo.configure(scrollregion=self._lienzo.bbox("all"))

    # ----- Métodos con el mismo nombre que en ttk.Treeview -----

    def delete(self, *skus: str) -> None:
        for sku in skus or tuple(self._orden):
            tarjeta = self._tarjetas.pop(sku, None)
            if tarjeta is not None:
                tarjeta.destroy()
                self._orden.remove(sku)
        if self._seleccion not in self._tarjetas:
            self._seleccion = None
        self._columnas = 0
        self._lienzo.yview_moveto(0)

    def get_children(self) -> tuple[str, ...]:
        return tuple(self._orden)

    def exists(self, sku: str) -> bool:
        return sku in self._tarjetas

    def selection(self) -> tuple[str, ...]:
        return (self._seleccion,) if self._seleccion else ()

    def selection_set(self, sku: str) -> None:
        if sku not in self._tarjetas:
            return
        cambio = sku != self._seleccion
        self._seleccion = sku
        for clave, tarjeta in self._tarjetas.items():
            tarjeta.marcar(clave == sku)
        if cambio:
            self.event_generate("<<Seleccion>>", when="tail")

    def selection_remove(self, *_skus) -> None:
        self._seleccion = None
        for tarjeta in self._tarjetas.values():
            tarjeta.marcar(False)

    def see(self, sku: str) -> None:
        tarjeta = self._tarjetas.get(sku)
        if tarjeta is None:
            return
        self.update_idletasks()
        alto_total = max(self._interior.winfo_height(), 1)
        self._lienzo.yview_moveto(max(0, tarjeta.winfo_y() - SEPARACION) / alto_total)
