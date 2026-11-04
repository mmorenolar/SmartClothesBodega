"""Ventana principal: menú lateral oscuro y área de contenido."""

import tkinter as tk
from tkinter import ttk

from smartclothes.controladores.controlador import Controlador
from smartclothes.vista import tema
from smartclothes.vista.comun import COLORES, MODULOS, informar
from smartclothes.vista.comprobantes import Comprobantes
from smartclothes.vista.inicio import Inicio
from smartclothes.vista.mermas import Mermas
from smartclothes.vista.productos import Productos
from smartclothes.vista.tiendas import Tiendas
from smartclothes.vista.traslados import Traslados


class BotonNav(tk.Frame):
    """Opción del menú lateral: ícono + texto, cambia de color al pasar el mouse."""

    def __init__(self, master, icono: str, texto: str, comando):
        super().__init__(master, bg=COLORES["lateral"], cursor="hand2")
        self._comando = comando
        self._activo = False
        self._barra = tk.Frame(self, bg=COLORES["lateral"], width=4)
        self._barra.pack(side="left", fill="y")
        self._icono = tk.Label(self, text=icono, width=2, bg=COLORES["lateral"], fg=COLORES["lateral_texto"],
                               font=tema.fuente(13))
        self._icono.pack(side="left", padx=(14, 8), pady=9)
        self._texto = tk.Label(self, text=texto, anchor="w", bg=COLORES["lateral"], fg=COLORES["lateral_texto"],
                               font=tema.fuente(10))
        self._texto.pack(side="left", fill="x", expand=True)
        for widget in (self, self._icono, self._texto):
            widget.bind("<Button-1>", lambda _e: self.invoke())
            widget.bind("<Enter>", lambda _e: self._pintar(encima=True))
            widget.bind("<Leave>", lambda _e: self._pintar(encima=False))

    def invoke(self) -> None:
        self._comando()

    def activar(self, activo: bool) -> None:
        self._activo = activo
        self._pintar(encima=False)

    def _pintar(self, encima: bool) -> None:
        fondo = COLORES["lateral_hover"] if (self._activo or encima) else COLORES["lateral"]
        texto = "#ffffff" if self._activo else (COLORES["lateral_texto"] if not encima else "#e4e8f0")
        for widget in (self, self._icono, self._texto):
            widget.configure(bg=fondo)
        self._icono.configure(fg=COLORES["acento"] if self._activo else texto)
        self._texto.configure(fg=texto, font=tema.fuente(10, "bold" if self._activo else "normal"))
        self._barra.configure(bg=COLORES["acento"] if self._activo else fondo)


class Aplicacion(tk.Tk):
    def __init__(self, controlador: Controlador):
        super().__init__()
        self.controlador = controlador
        self.title("Smart Clothes — Bodega principal")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        tema.aplicar(self)
        self._crear_menu()

        lateral = tk.Frame(self, bg=COLORES["lateral"], width=230)
        lateral.pack(side="left", fill="y")
        lateral.pack_propagate(False)
        marca = tk.Frame(lateral, bg=COLORES["lateral"], padx=20, pady=22)
        marca.pack(fill="x")
        logo = tk.Label(marca, text="SC", bg=COLORES["acento"], fg="#ffffff", width=3,
                        font=tema.fuente(12, "bold"), pady=4)
        logo.pack(side="left")
        nombres = tk.Frame(marca, bg=COLORES["lateral"])
        nombres.pack(side="left", padx=(10, 0))
        tk.Label(nombres, text="Smart Clothes", bg=COLORES["lateral"], fg="#ffffff",
                 font=tema.fuente(12, "bold")).pack(anchor="w")
        tk.Label(nombres, text="Bodega principal", bg=COLORES["lateral"], fg=COLORES["lateral_texto"],
                 font=tema.fuente(9)).pack(anchor="w")
        tk.Label(lateral, text="MÓDULOS", bg=COLORES["lateral"], fg="#6c7689",
                 font=tema.fuente(8, "bold")).pack(anchor="w", padx=22, pady=(8, 6))

        self._botones_nav: dict[str, BotonNav] = {}
        for indice, (clave, etiqueta, icono, _subtitulo) in enumerate(MODULOS, start=1):
            boton = BotonNav(lateral, icono, etiqueta, lambda destino=clave: self.mostrar(destino))
            boton.pack(fill="x")
            self._botones_nav[clave] = boton
            self.bind_all(f"<Control-Key-{indice}>", lambda _e, destino=clave: self.mostrar(destino))
        tk.Label(lateral, text="Atajos: Ctrl + 1 … 6", bg=COLORES["lateral"], fg="#6c7689",
                 font=tema.fuente(8)).pack(side="bottom", anchor="w", padx=22, pady=16)

        self._contenido = ttk.Frame(self)
        self._contenido.pack(side="left", fill="both", expand=True)
        self._pantallas = {
            "inicio": Inicio(self._contenido, controlador, self.mostrar, self.ver_producto),
            "productos": Productos(self._contenido, controlador),
            "tiendas": Tiendas(self._contenido, controlador),
            "traslados": Traslados(self._contenido, controlador, self.ver_comprobante),
            "mermas": Mermas(self._contenido, controlador, self.ver_comprobante),
            "comprobantes": Comprobantes(self._contenido, controlador),
        }
        self._actual = None
        self.mostrar("inicio")

    def _crear_menu(self) -> None:
        barra = tk.Menu(self)
        archivo = tk.Menu(barra, tearoff=0)
        archivo.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Archivo", menu=archivo)
        modulos = tk.Menu(barra, tearoff=0)
        for indice, (clave, etiqueta, _icono, _sub) in enumerate(MODULOS, start=1):
            modulos.add_command(label=etiqueta, accelerator=f"Ctrl+{indice}",
                                command=lambda destino=clave: self.mostrar(destino))
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
            boton.activar(clave == nombre)

    def ver_comprobante(self, folio: str) -> None:
        self._pantallas["comprobantes"].seleccionar(folio, animar=True)
        self.mostrar("comprobantes")

    def ver_producto(self, sku: str) -> None:
        self.mostrar("productos")
        self._pantallas["productos"].seleccionar(sku)


def iniciar(directorio=None) -> None:
    controlador = Controlador(directorio)
    aplicacion = Aplicacion(controlador)
    if controlador.advertencia:
        aplicacion.after(400, lambda: informar(aplicacion, "Datos", controlador.advertencia))
    aplicacion.mainloop()
