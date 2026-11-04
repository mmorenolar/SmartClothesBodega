"""Creación de órdenes de traslado, carga de prendas por SKU y confirmación."""

import tkinter as tk
from datetime import date
from tkinter import ttk

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.vista.comun import (
    Pantalla,
    configurar_combo,
    crear_tabla,
    informar,
    mostrar_error,
    pedir_confirmacion,
    titulo,
)


class Traslados(Pantalla):
    def __init__(self, master, controlador, ver_comprobante):
        super().__init__(master, controlador)
        self._ver_comprobante = ver_comprobante
        self._tiendas: dict[str, str] = {}
        self._folio: str | None = None
        titulo(self, "Órdenes de traslado")

        alta = ttk.LabelFrame(self, text="Nueva orden", padding=12)
        alta.pack(fill="x")
        self.tienda = tk.StringVar()
        self.fecha = tk.StringVar(value=date.today().strftime("%d-%m-%Y"))
        ttk.Label(alta, text="Tienda destino").grid(row=0, column=0, sticky="w")
        self.combo_tienda = ttk.Combobox(alta, textvariable=self.tienda, state="readonly")
        self.combo_tienda.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Label(alta, text="Fecha de despacho (dd-mm-aaaa)").grid(row=0, column=2, sticky="w")
        ttk.Entry(alta, textvariable=self.fecha, width=12).grid(row=0, column=3, padx=8)
        ttk.Button(alta, text="Crear orden", command=self.crear).grid(row=0, column=4)
        alta.columnconfigure(1, weight=1)

        marco, self.tabla = crear_tabla(
            self,
            ("folio", "fecha", "tienda", "estado", "unidades"),
            ("Folio", "Despacho", "Tienda destino", "Estado", "Unidades"),
            (110, 100, 280, 110, 90),
            altura=4,
        )
        marco.pack(fill="both", expand=True, pady=12)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

        edicion = ttk.LabelFrame(self, text="Prendas de la orden seleccionada", padding=12)
        edicion.pack(fill="both", expand=True)
        self.sku = tk.StringVar()
        self.cantidad = tk.StringVar(value="1")
        ttk.Label(edicion, text="SKU").grid(row=0, column=0, sticky="w")
        self.combo_sku = ttk.Combobox(edicion, textvariable=self.sku, width=18)
        self.combo_sku.grid(row=0, column=1, sticky="w", padx=8)
        self.combo_sku.bind("<<ComboboxSelected>>", lambda _evento: self._describir_sku())
        self.combo_sku.bind("<KeyRelease>", lambda _evento: self._describir_sku())
        ttk.Label(edicion, text="Cantidad").grid(row=0, column=2, sticky="w")
        ttk.Entry(edicion, textvariable=self.cantidad, width=8).grid(row=0, column=3, padx=8)
        self.boton_agregar = ttk.Button(edicion, text="Agregar", command=self.agregar)
        self.boton_quitar = ttk.Button(edicion, text="Quitar línea", command=self.quitar)
        self.boton_agregar.grid(row=0, column=4, padx=(0, 8))
        self.boton_quitar.grid(row=0, column=5)
        self.info_sku = ttk.Label(edicion, foreground="#5a4a3a")
        self.info_sku.grid(row=1, column=0, columnspan=6, sticky="w", pady=(6, 0))

        marco_lineas, self.lineas = crear_tabla(
            edicion,
            ("sku", "nombre", "talla", "color", "cantidad"),
            ("SKU", "Nombre", "Talla", "Color", "Cantidad"),
            (140, 240, 70, 110, 90),
            altura=4,
        )
        marco_lineas.grid(row=2, column=0, columnspan=6, sticky="nsew", pady=(8, 0))
        edicion.rowconfigure(2, weight=1)
        edicion.columnconfigure(6, weight=1)

        despacho = ttk.LabelFrame(edicion, text="Despacho", padding=8)
        despacho.grid(row=3, column=0, columnspan=7, sticky="ew", pady=(8, 0))
        self.transporte = tk.StringVar()
        ttk.Label(despacho, text="Transporte").grid(row=0, column=0, sticky="w")
        self.combo_transporte = ttk.Combobox(
            despacho, textvariable=self.transporte, values=controlador.transportes(), state="readonly", width=24
        )
        self.combo_transporte.grid(row=0, column=1, sticky="w", padx=8)
        self.cotizacion = ttk.Label(despacho, justify="left", foreground="#5a4a3a")
        self.cotizacion.grid(row=0, column=2, sticky="w", padx=(8, 0))

        pie = ttk.Frame(edicion)
        pie.grid(row=4, column=0, columnspan=7, sticky="ew", pady=(8, 0))
        self.totales = ttk.Label(pie)
        self.totales.pack(side="left")
        self.boton_anular = ttk.Button(pie, text="Anular orden", command=self.anular)
        self.boton_confirmar = ttk.Button(pie, text="Confirmar y emitir comprobante", command=self.confirmar)
        self.boton_anular.pack(side="right")
        self.boton_confirmar.pack(side="right", padx=8)

    def refrescar(self) -> None:
        self._tiendas = {tienda.identificacion: tienda.codigo for tienda in self.controlador.listar_tiendas()}
        configurar_combo(self.combo_tienda, list(self._tiendas), self.tienda.get())
        self.combo_sku["values"] = [producto.sku for producto in self.controlador.listar_productos()]

        seleccionado = self._folio
        self.tabla.delete(*self.tabla.get_children())
        for orden in reversed(self.controlador.listar_ordenes()):
            self.tabla.insert(
                "",
                "end",
                iid=orden.folio,
                values=(
                    orden.folio,
                    orden.fecha_texto,
                    self.controlador.nombre_tienda(orden.tienda_codigo),
                    orden.estado.etiqueta,
                    orden.unidades,
                ),
            )
        if seleccionado and self.tabla.exists(seleccionado):
            self.tabla.selection_set(seleccionado)
            self.tabla.see(seleccionado)
            self._mostrar(seleccionado)
        else:
            self._folio = None
            self._mostrar(None)
        self._describir_sku()

    def _describir_sku(self) -> None:
        texto = self.sku.get().strip()
        if not texto:
            self.info_sku.configure(text="Escribe o elige un SKU.")
            return
        try:
            producto = self.controlador.obtener_producto(texto)
        except ReglaNegocioError:
            self.info_sku.configure(text="SKU no encontrado.")
            return
        self.info_sku.configure(
            text=(
                f"{producto.descripcion()} — Stock {producto.stock} · "
                f"Disponible para traslado {self.controlador.stock_disponible(producto.sku)} · "
                f"{producto.estado.etiqueta}"
            )
        )

    def crear(self) -> None:
        codigo = self._tiendas.get(self.tienda.get(), "")
        ok, orden = self.ejecutar(lambda: self.controlador.crear_orden(codigo, self.fecha.get()))
        if not ok:
            return
        self._folio = orden.folio
        informar(self.winfo_toplevel(), "Orden creada", f"Orden {orden.folio} en borrador. Agrega las prendas.")
        self.refrescar()

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        self._folio = seleccion[0] if seleccion else None
        self._mostrar(self._folio)

    def _mostrar(self, folio: str | None) -> None:
        self.lineas.delete(*self.lineas.get_children())
        if not folio:
            self.totales.configure(text="Selecciona o crea una orden.")
            self.cotizacion.configure(text="")
            self._habilitar({})
            return
        orden = self.controlador.obtener_orden(folio)
        for detalle in orden.detalles:
            self.lineas.insert(
                "",
                "end",
                iid=detalle.sku,
                values=(detalle.sku, detalle.nombre, detalle.talla, detalle.color, detalle.cantidad),
            )
        self.totales.configure(
            text=f"{orden.folio} · {orden.estado.etiqueta} · {len(orden.detalles)} líneas · {orden.unidades} unidades"
        )
        self._mostrar_despacho(orden)
        self._habilitar(self.controlador.acciones(folio))

    def _mostrar_despacho(self, orden) -> None:
        """Muestra lo que cotiza cada camión y propone el más conveniente."""
        if orden.despacho is not None and orden.aplicada:
            self.transporte.set(orden.despacho.nombre)
            self.cotizacion.configure(text=f"Despachada: {orden.despacho.resumen()}")
            self.combo_transporte.configure(state="disabled")
            return
        filas = self.controlador.cotizar_despachos(orden.folio)
        self.cotizacion.configure(text="\n".join(f"{nombre}: {texto}" for nombre, texto in filas))
        sugerido = self.controlador.transporte_sugerido(orden.folio)
        self.transporte.set(sugerido)
        self.combo_transporte.configure(state="readonly" if orden.detalles else "disabled")

    def _habilitar(self, acciones: dict[str, bool]) -> None:
        def estado(clave: str) -> str:
            return "normal" if acciones.get(clave) else "disabled"

        self.boton_agregar.configure(state=estado("puede_editar_items"))
        self.boton_quitar.configure(state=estado("puede_editar_items"))
        self.boton_confirmar.configure(state=estado("puede_confirmar"))
        self.boton_anular.configure(state=estado("puede_anular"))

    def agregar(self) -> None:
        if not self._folio:
            mostrar_error(self.winfo_toplevel(), "Selecciona una orden.")
            return
        ok, _orden = self.ejecutar(
            lambda: self.controlador.agregar_a_orden(self._folio, self.sku.get(), self.cantidad.get())
        )
        if not ok:
            return
        self.cantidad.set("1")
        self.refrescar()

    def quitar(self) -> None:
        if not self._folio:
            mostrar_error(self.winfo_toplevel(), "Selecciona una orden.")
            return
        seleccion = self.lineas.selection()
        if not seleccion:
            mostrar_error(self.winfo_toplevel(), "Selecciona la línea que quieres quitar.")
            return
        ok, _orden = self.ejecutar(lambda: self.controlador.quitar_de_orden(self._folio, seleccion[0]))
        if ok:
            self.refrescar()

    def confirmar(self) -> None:
        if not self._folio:
            mostrar_error(self.winfo_toplevel(), "Selecciona una orden.")
            return
        folio = self._folio
        if not pedir_confirmacion(
            self.winfo_toplevel(),
            "Confirmar traslado",
            f"¿Confirmar la orden {folio} con {self.transporte.get() or 'el transporte elegido'}? "
            "Las unidades se descuentan de la bodega y no se puede deshacer.",
        ):
            return
        ok, _comprobante = self.ejecutar(lambda: self.controlador.confirmar_orden(folio, self.transporte.get()))
        if not ok:
            self.refrescar()
            return
        informar(self.winfo_toplevel(), "Traslado confirmado", f"Stock descontado. Comprobante {folio} emitido.")
        self.refrescar()
        self._ver_comprobante(folio)

    def anular(self) -> None:
        if not self._folio:
            mostrar_error(self.winfo_toplevel(), "Selecciona una orden.")
            return
        if not pedir_confirmacion(self.winfo_toplevel(), "Anular orden", f"¿Anular la orden {self._folio}?"):
            return
        ok, _orden = self.ejecutar(lambda: self.controlador.anular_orden(self._folio))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Orden anulada", "La reserva de stock quedó liberada.")
        self.refrescar()
