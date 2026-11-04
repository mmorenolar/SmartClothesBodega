"""Tiendas: tabla a la izquierda y ficha para crear o editar a la derecha."""

import tkinter as tk
from tkinter import ttk

from smartclothes.vista.comun import (
    COLORES,
    Pantalla,
    Tarjeta,
    crear_tabla,
    encabezado,
    etiqueta_campo,
    fila,
    informar,
    mostrar_error,
    pedir_confirmacion,
)


class Tiendas(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._codigo: str | None = None
        cabecera = encabezado(self, "Tiendas", "Tiendas de venta al público que piden reabastecimiento.")
        ttk.Button(cabecera, text="+  Nueva tienda", style="Primario.TButton", command=self.limpiar).pack(side="right")

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        tarjeta_tabla = Tarjeta(cuerpo, padding=8)
        tarjeta_tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        marco, self.tabla = crear_tabla(
            tarjeta_tabla,
            ("codigo", "nombre", "direccion", "ordenes"),
            ("Código", "Nombre", "Dirección", "Órdenes"),
            (100, 190, 230, 70),
        )
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

        panel = Tarjeta(cuerpo, width=340)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_propagate(False)
        panel.columnconfigure(0, weight=1)
        self.lbl_panel = ttk.Label(panel, text="Nueva tienda", style="Seccion.TLabel")
        self.lbl_panel.grid(row=0, column=0, sticky="w", pady=(0, 12))

        self.codigo = tk.StringVar()
        self.nombre = tk.StringVar()
        self.direccion = tk.StringVar()
        etiqueta_campo(panel, "Código (ej.: T-CENTRO)").grid(row=1, column=0, sticky="w")
        self.codigo_entry = ttk.Entry(panel, textvariable=self.codigo)
        self.codigo_entry.grid(row=2, column=0, sticky="ew", pady=(2, 10))
        etiqueta_campo(panel, "Nombre").grid(row=3, column=0, sticky="w")
        ttk.Entry(panel, textvariable=self.nombre).grid(row=4, column=0, sticky="ew", pady=(2, 10))
        etiqueta_campo(panel, "Dirección").grid(row=5, column=0, sticky="w")
        ttk.Entry(panel, textvariable=self.direccion).grid(row=6, column=0, sticky="ew", pady=(2, 14))

        acciones = tk.Frame(panel, bg=COLORES["tarjeta"])
        acciones.grid(row=7, column=0, sticky="ew")
        self.boton_registrar = ttk.Button(acciones, text="Registrar tienda", style="Primario.TButton",
                                          command=self.registrar)
        self.boton_guardar = ttk.Button(acciones, text="Guardar cambios", style="Primario.TButton",
                                        command=self.guardar)
        self.boton_limpiar = ttk.Button(acciones, text="Cancelar", command=self.limpiar)
        self.boton_eliminar = ttk.Button(acciones, text="Eliminar", style="Peligro.TButton", command=self.eliminar)
        self.boton_limpiar.pack(side="left", padx=6)
        self.boton_eliminar.pack(side="right")
        self.ayuda = ttk.Label(panel, style="Ayuda.TLabel", wraplength=290, justify="left",
                               text="Una tienda con órdenes de traslado no se puede eliminar.")
        self.ayuda.grid(row=8, column=0, sticky="w", pady=(14, 0))
        self.limpiar()

    def refrescar(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        for tienda in self.controlador.listar_tiendas():
            fila(self.tabla, tienda.codigo, (tienda.codigo, tienda.nombre, tienda.direccion,
                                             self.controlador.ordenes_de_tienda(tienda.codigo)))
        if self._codigo and self.tabla.exists(self._codigo):
            self.tabla.selection_set(self._codigo)

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        tienda = self.controlador.obtener_tienda(seleccion[0])
        self._codigo = tienda.codigo
        self.codigo.set(tienda.codigo)
        self.nombre.set(tienda.nombre)
        self.direccion.set(tienda.direccion)
        self.codigo_entry.state(["disabled"])
        self.lbl_panel.configure(text="Editar tienda")
        self.boton_registrar.pack_forget()
        self.boton_guardar.pack(side="left", before=self.boton_limpiar)
        self.boton_eliminar.pack(side="right")

    def limpiar(self) -> None:
        self._codigo = None
        for variable in (self.codigo, self.nombre, self.direccion):
            variable.set("")
        self.codigo_entry.state(["!disabled"])
        self.lbl_panel.configure(text="Nueva tienda")
        self.boton_guardar.pack_forget()
        self.boton_registrar.pack(side="left", before=self.boton_limpiar)
        self.boton_eliminar.pack_forget()
        if self.tabla.selection():
            self.tabla.selection_remove(self.tabla.selection())

    def registrar(self) -> None:
        ok, tienda = self.ejecutar(
            lambda: self.controlador.registrar_tienda(self.codigo.get(), self.nombre.get(), self.direccion.get())
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Tienda registrada", f"{tienda.nombre} ya puede recibir traslados.")
        self.limpiar()
        self.refrescar()

    def guardar(self) -> None:
        if not self._codigo:
            mostrar_error(self.winfo_toplevel(), "Selecciona una tienda de la tabla para editarla.")
            return
        ok, _tienda = self.ejecutar(
            lambda: self.controlador.editar_tienda(self._codigo, self.nombre.get(), self.direccion.get())
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Cambios guardados", "La tienda quedó actualizada.")
        self.refrescar()

    def eliminar(self) -> None:
        if not self._codigo:
            mostrar_error(self.winfo_toplevel(), "Selecciona una tienda de la tabla para eliminarla.")
            return
        if not pedir_confirmacion(self.winfo_toplevel(), "Eliminar tienda", f"¿Eliminar la tienda {self._codigo}?"):
            return
        ok, _resultado = self.ejecutar(lambda: self.controlador.eliminar_tienda(self._codigo))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Tienda eliminada", "La tienda salió del registro.")
        self.limpiar()
        self.refrescar()
