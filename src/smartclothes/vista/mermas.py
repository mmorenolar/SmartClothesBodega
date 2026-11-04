"""Registro de bajas por daño, pérdida o falla de fábrica."""

import tkinter as tk
from tkinter import ttk

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.vista.comun import Pantalla, configurar_combo, crear_tabla, informar, pedir_confirmacion, titulo


class Mermas(Pantalla):
    def __init__(self, master, controlador, ver_comprobante):
        super().__init__(master, controlador)
        self._ver_comprobante = ver_comprobante
        titulo(self, "Mermas y pérdidas")
        ttk.Label(
            self,
            text="La baja descuenta el stock en el momento y emite un Registro de Merma con folio propio.",
        ).pack(anchor="w", pady=(0, 8))

        formulario = ttk.LabelFrame(self, text="Nueva merma", padding=12)
        formulario.pack(fill="x")
        self.sku = tk.StringVar()
        self.cantidad = tk.StringVar(value="1")
        self.motivo = tk.StringVar()
        ttk.Label(formulario, text="SKU").grid(row=0, column=0, sticky="w", pady=4)
        self.combo_sku = ttk.Combobox(formulario, textvariable=self.sku, width=18)
        self.combo_sku.grid(row=0, column=1, sticky="w", padx=8, pady=4)
        self.combo_sku.bind("<<ComboboxSelected>>", lambda _evento: self._describir_sku())
        self.combo_sku.bind("<KeyRelease>", lambda _evento: self._describir_sku())
        ttk.Label(formulario, text="Cantidad").grid(row=0, column=2, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.cantidad, width=8).grid(row=0, column=3, padx=8, pady=4)
        ttk.Label(formulario, text="Motivo").grid(row=0, column=4, sticky="w", pady=4)
        self.combo_motivo = ttk.Combobox(formulario, textvariable=self.motivo, state="readonly", width=18)
        self.combo_motivo.grid(row=0, column=5, sticky="w", padx=8, pady=4)
        self.info_sku = ttk.Label(formulario, foreground="#5a4a3a")
        self.info_sku.grid(row=1, column=0, columnspan=6, sticky="w")
        ttk.Label(formulario, text="Observación").grid(row=2, column=0, sticky="nw", pady=(8, 0))
        self.observacion = tk.Text(formulario, height=3, width=60, wrap="word", relief="solid", borderwidth=1)
        self.observacion.grid(row=2, column=1, columnspan=5, sticky="ew", padx=8, pady=(8, 0))
        formulario.columnconfigure(5, weight=1)
        ttk.Button(formulario, text="Registrar merma", command=self.registrar).grid(
            row=3, column=0, columnspan=6, sticky="e", pady=(12, 0)
        )

        marco, self.tabla = crear_tabla(
            self,
            ("folio", "fecha", "sku", "nombre", "cantidad", "motivo", "observacion"),
            ("Folio", "Fecha", "SKU", "Nombre", "Cantidad", "Motivo", "Observación"),
            (100, 90, 120, 160, 70, 120, 280),
        )
        marco.pack(fill="both", expand=True, pady=(12, 0))
        self.tabla.bind("<Double-1>", lambda _evento: self._abrir_seleccion())
        ttk.Label(self, text="Doble clic en una fila para ver su comprobante.").pack(anchor="w", pady=(4, 0))

    def refrescar(self) -> None:
        self.combo_sku["values"] = [producto.sku for producto in self.controlador.listar_productos()]
        configurar_combo(self.combo_motivo, list(self.controlador.motivos_merma()), self.motivo.get())
        self.tabla.delete(*self.tabla.get_children())
        for merma in reversed(self.controlador.listar_mermas()):
            self.tabla.insert(
                "",
                "end",
                iid=merma.folio,
                values=(
                    merma.folio,
                    merma.fecha_texto,
                    merma.sku,
                    merma.nombre,
                    merma.cantidad,
                    merma.motivo.etiqueta,
                    merma.observacion,
                ),
            )
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
        self.info_sku.configure(text=f"{producto.descripcion()} — Stock {producto.stock} · {producto.estado.etiqueta}")

    def registrar(self) -> None:
        observacion = self.observacion.get("1.0", "end").strip()
        if not pedir_confirmacion(
            self.winfo_toplevel(),
            "Registrar merma",
            f"¿Dar de baja {self.cantidad.get().strip()} unidad(es) de {self.sku.get().strip().upper()}?",
        ):
            return
        ok, merma = self.ejecutar(
            lambda: self.controlador.registrar_merma(self.sku.get(), self.cantidad.get(), self.motivo.get(), observacion)
        )
        if not ok:
            return
        producto = self.controlador.obtener_producto(merma.sku)
        informar(
            self.winfo_toplevel(),
            "Merma registrada",
            f"{merma.folio}: stock de {producto.sku} ahora {producto.stock} ({producto.estado.etiqueta}).",
        )
        self.cantidad.set("1")
        self.observacion.delete("1.0", "end")
        self.refrescar()
        self._ver_comprobante(merma.folio)

    def _abrir_seleccion(self) -> None:
        seleccion = self.tabla.selection()
        if seleccion:
            self._ver_comprobante(seleccion[0])
