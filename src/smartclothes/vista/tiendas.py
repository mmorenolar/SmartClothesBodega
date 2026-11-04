"""Alta, edición y eliminación de las tiendas que reciben traslados."""

import tkinter as tk
from tkinter import ttk

from smartclothes.vista.comun import Pantalla, crear_tabla, informar, mostrar_error, pedir_confirmacion, titulo


class Tiendas(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._codigo: str | None = None
        titulo(self, "Tiendas")
        ttk.Label(self, text="Tiendas de venta al público que piden reabastecimiento a la bodega.").pack(
            anchor="w", pady=(0, 8)
        )

        formulario = ttk.LabelFrame(self, text="Datos de la tienda", padding=12)
        formulario.pack(fill="x")
        self.codigo = tk.StringVar()
        self.nombre = tk.StringVar()
        self.direccion = tk.StringVar()
        ttk.Label(formulario, text="Código").grid(row=0, column=0, sticky="w", pady=4)
        self.codigo_entry = ttk.Entry(formulario, textvariable=self.codigo)
        self.codigo_entry.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=4)
        ttk.Label(formulario, text="Nombre").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.nombre).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=4)
        ttk.Label(formulario, text="Dirección").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.direccion).grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=4)
        formulario.columnconfigure(1, weight=1)

        acciones = ttk.Frame(formulario)
        acciones.grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))
        self.boton_registrar = ttk.Button(acciones, text="Registrar", command=self.registrar)
        self.boton_guardar = ttk.Button(acciones, text="Guardar cambios", command=self.guardar)
        self.boton_eliminar = ttk.Button(acciones, text="Eliminar", command=self.eliminar)
        self.boton_limpiar = ttk.Button(acciones, text="Limpiar", command=self.limpiar)
        for boton in (self.boton_registrar, self.boton_guardar, self.boton_eliminar, self.boton_limpiar):
            boton.pack(side="left", padx=(0, 8))

        marco, self.tabla = crear_tabla(
            self,
            ("codigo", "nombre", "direccion"),
            ("Código", "Nombre", "Dirección"),
            (120, 240, 360),
        )
        marco.pack(fill="both", expand=True, pady=(12, 0))
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)
        self.limpiar()

    def refrescar(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        for tienda in self.controlador.listar_tiendas():
            self.tabla.insert("", "end", iid=tienda.codigo, values=(tienda.codigo, tienda.nombre, tienda.direccion))

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        tienda = self.controlador.obtener_tienda(seleccion[0])
        self._codigo = tienda.codigo
        self.codigo.set(tienda.codigo)
        self.nombre.set(tienda.nombre)
        self.direccion.set(tienda.direccion)
        self.codigo_entry.configure(state="disabled")
        self.boton_registrar.configure(state="disabled")
        self.boton_guardar.configure(state="normal")
        self.boton_eliminar.configure(state="normal")

    def limpiar(self) -> None:
        self._codigo = None
        for variable in (self.codigo, self.nombre, self.direccion):
            variable.set("")
        self.codigo_entry.configure(state="normal")
        self.boton_registrar.configure(state="normal")
        self.boton_guardar.configure(state="disabled")
        self.boton_eliminar.configure(state="disabled")
        if self.tabla.selection():
            self.tabla.selection_remove(self.tabla.selection())

    def registrar(self) -> None:
        ok, _tienda = self.ejecutar(
            lambda: self.controlador.registrar_tienda(self.codigo.get(), self.nombre.get(), self.direccion.get())
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Tienda registrada", "La tienda ya puede recibir traslados.")
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
        informar(self.winfo_toplevel(), "Tienda actualizada", "Los cambios quedaron guardados.")
        self.limpiar()
        self.refrescar()

    def eliminar(self) -> None:
        if not self._codigo:
            mostrar_error(self.winfo_toplevel(), "Selecciona una tienda de la tabla para eliminarla.")
            return
        if not pedir_confirmacion(self.winfo_toplevel(), "Eliminar tienda", "¿Eliminar la tienda seleccionada?"):
            return
        ok, _resultado = self.ejecutar(lambda: self.controlador.eliminar_tienda(self._codigo))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Tienda eliminada", "La tienda salió del registro.")
        self.limpiar()
        self.refrescar()
