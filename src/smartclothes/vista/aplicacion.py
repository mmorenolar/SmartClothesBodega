"""Ventana principal y menú de navegación."""

import tkinter as tk
from tkinter import ttk

from smartclothes.controladores.controlador import Controlador
from smartclothes.vista.comun import ACENTO, FONDO, MODULOS, informar
from smartclothes.vista.comprobantes import Comprobantes
from smartclothes.vista.inicio import Inicio
from smartclothes.vista.mermas import Mermas
from smartclothes.vista.productos import Productos
from smartclothes.vista.tiendas import Tiendas
from smartclothes.vista.traslados import Traslados


class Aplicacion(tk.Tk):
    def __init__(self, controlador: Controlador):
        super().__init__()
        self.controlador = controlador
        self.title("Smart Clothes — Bodega principal")
        self.geometry("1220x760")
        self.minsize(1000, 640)
        self._aplicar_estilo()
        self._crear_menu()
        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        self._navegacion = ttk.Frame(cuerpo, padding=(12, 16, 8, 16))
        self._navegacion.pack(side="left", fill="y")
        ttk.Label(self._navegacion, text="Smart Clothes", style="Marca.TLabel").pack(anchor="w")
        ttk.Label(self._navegacion, text="Bodega principal").pack(anchor="w", pady=(0, 16))
        self._contenido = ttk.Frame(cuerpo)
        self._contenido.pack(side="left", fill="both", expand=True)
        self._botones_nav = {}
        for clave, etiqueta in MODULOS:
            boton = ttk.Button(
                self._navegacion,
                text=etiqueta,
                style="Nav.TButton",
                command=lambda destino=clave: self.mostrar(destino),
            )
            boton.pack(fill="x", pady=3)
            self._botones_nav[clave] = boton
        self._pantallas = {
            "inicio": Inicio(self._contenido, controlador, self.mostrar),
            "productos": Productos(self._contenido, controlador),
            "tiendas": Tiendas(self._contenido, controlador),
            "traslados": Traslados(self._contenido, controlador, self.ver_comprobante),
            "mermas": Mermas(self._contenido, controlador, self.ver_comprobante),
            "comprobantes": Comprobantes(self._contenido, controlador),
        }
        self._actual = None
        self.mostrar("inicio")

    def _aplicar_estilo(self) -> None:
        self.configure(background=FONDO)
        estilo = ttk.Style(self)
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        for clase in (".", "TFrame", "TLabel", "TLabelframe", "TLabelframe.Label", "TCheckbutton"):
            estilo.configure(clase, background=FONDO)
        estilo.configure("Titulo.TLabel", font=("Helvetica", 20, "bold"))
        estilo.configure("Marca.TLabel", font=("Helvetica", 16, "bold"))
        estilo.configure("Dato.TLabel", font=("Helvetica", 12))
        estilo.configure("TButton", padding=6)
        estilo.configure("Nav.TButton", padding=(12, 8), anchor="w")
        estilo.configure("NavActivo.TButton", padding=(12, 8), anchor="w", background=ACENTO)
        estilo.configure("Treeview", rowheight=26)
        estilo.configure("Fotos.Treeview", rowheight=58)
        estilo.configure("Treeview.Heading", font=("Helvetica", 11, "bold"))

    def _crear_menu(self) -> None:
        barra = tk.Menu(self)
        archivo = tk.Menu(barra, tearoff=0)
        archivo.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Archivo", menu=archivo)
        modulos = tk.Menu(barra, tearoff=0)
        for clave, etiqueta in MODULOS:
            modulos.add_command(label=etiqueta, command=lambda destino=clave: self.mostrar(destino))
        barra.add_cascade(label="Módulos", menu=modulos)
        self.configure(menu=barra)

    def mostrar(self, nombre: str) -> None:
        if self._actual is not None:
            self._actual.pack_forget()
        pantalla = self._pantallas[nombre]
        pantalla.refrescar()
        pantalla.pack(fill="both", expand=True)
        self._actual = pantalla
        for clave, boton in self._botones_nav.items():
            boton.configure(style="NavActivo.TButton" if clave == nombre else "Nav.TButton")

    def ver_comprobante(self, folio: str) -> None:
        self._pantallas["comprobantes"].seleccionar(folio)
        self.mostrar("comprobantes")


def iniciar(directorio=None) -> None:
    controlador = Controlador(directorio)
    aplicacion = Aplicacion(controlador)
    if controlador.advertencia:
        aplicacion.after(200, lambda: informar(aplicacion, "Datos", controlador.advertencia))
    aplicacion.mainloop()
