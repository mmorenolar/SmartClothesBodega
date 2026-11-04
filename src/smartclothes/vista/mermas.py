"""Mermas: formulario guiado a la izquierda e historial a la derecha."""

import tkinter as tk
from tkinter import ttk

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.vista import tema
from smartclothes.vista.comun import (
    COLORES,
    ComboBuscador,
    Pantalla,
    Tarjeta,
    cargar_miniatura,
    chip,
    chip_estado_producto,
    crear_tabla,
    encabezado,
    etiqueta_campo,
    fila,
    informar,
    pedir_confirmacion,
    pintar_chip,
)

MINIMO_OBSERVACION = 10


class Mermas(Pantalla):
    def __init__(self, master, controlador, ver_comprobante):
        super().__init__(master, controlador)
        self._ver_comprobante = ver_comprobante
        self._miniatura: tk.PhotoImage | None = None
        encabezado(self, "Mermas y pérdidas", "La baja descuenta el stock al instante y emite un Registro de Merma.")

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        formulario = Tarjeta(cuerpo, width=400)
        formulario.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        formulario.pack_propagate(False)
        ttk.Label(formulario, text="Nueva merma", style="Seccion.TLabel").pack(anchor="w")

        self.sku = tk.StringVar()
        self.cantidad = tk.StringVar(value="1")
        self.motivo = tk.StringVar()

        etiqueta_campo(formulario, "SKU de la prenda").pack(anchor="w", pady=(12, 2))
        self.combo_sku = ComboBuscador(formulario, textvariable=self.sku)
        self.combo_sku.pack(fill="x")
        self.combo_sku.bind("<<ComboboxSelected>>", lambda _e: self._describir_sku())
        self.combo_sku.bind("<KeyRelease>", lambda _e: self._describir_sku(), add="+")

        ficha = tk.Frame(formulario, bg=COLORES["zebra"], padx=10, pady=8)
        ficha.pack(fill="x", pady=(8, 0))
        self.lbl_foto = tk.Label(ficha, bg=COLORES["zebra"], width=6, text="")
        self.lbl_foto.pack(side="left")
        textos = tk.Frame(ficha, bg=COLORES["zebra"])
        textos.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.info_sku = tk.Label(textos, bg=COLORES["zebra"], fg=COLORES["suave"], justify="left", anchor="w",
                                 wraplength=250, font=tema.fuente(9))
        self.info_sku.pack(anchor="w", fill="x")
        self.chip_stock = chip(textos, "", "neutro")

        etiqueta_campo(formulario, "Cantidad dada de baja").pack(anchor="w", pady=(12, 2))
        ttk.Spinbox(formulario, from_=1, to=9999, textvariable=self.cantidad, width=8).pack(anchor="w")

        etiqueta_campo(formulario, "Motivo").pack(anchor="w", pady=(12, 2))
        motivos = tk.Frame(formulario, bg=COLORES["tarjeta"])
        motivos.pack(fill="x")
        for motivo in controlador.motivos_merma():
            ttk.Radiobutton(motivos, text=motivo, value=motivo, variable=self.motivo,
                            style="Segmento.Toolbutton").pack(side="left", fill="x", expand=True, padx=(0, 4))

        etiqueta_campo(formulario, "Observación (justifica la baja)").pack(anchor="w", pady=(12, 2))
        self.observacion = tk.Text(formulario, height=4, wrap="word", relief="flat", highlightthickness=1,
                                   highlightbackground=COLORES["borde"], highlightcolor=COLORES["acento"],
                                   font=tema.fuente(10), padx=8, pady=6)
        self.observacion.pack(fill="x")
        self.observacion.bind("<KeyRelease>", lambda _e: self._contar())
        self.contador = ttk.Label(formulario, style="Ayuda.TLabel")
        self.contador.pack(anchor="e", pady=(2, 0))

        ttk.Button(formulario, text="Registrar merma", style="Primario.TButton", command=self.registrar).pack(
            fill="x", pady=(10, 0)
        )

        historial = Tarjeta(cuerpo, padding=14)
        historial.grid(row=0, column=1, sticky="nsew")
        cabeza = tk.Frame(historial, bg=COLORES["tarjeta"])
        cabeza.pack(fill="x", pady=(0, 8))
        ttk.Label(cabeza, text="Historial", style="Seccion.TLabel").pack(side="left")
        self.chip_total = chip(cabeza, "", "aviso")
        self.chip_total.pack(side="right")
        marco, self.tabla = crear_tabla(
            historial,
            ("folio", "fecha", "sku", "cantidad", "motivo"),
            ("Folio", "Fecha", "SKU", "Cant.", "Motivo"),
            (95, 90, 130, 55, 120),
        )
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<Double-1>", lambda _evento: self._abrir_seleccion())
        self.tabla.bind("<<TreeviewSelect>>", lambda _evento: self._mostrar_observacion())
        self.lbl_observacion = ttk.Label(historial, style="Ayuda.TLabel", wraplength=480, justify="left",
                                         text="Selecciona una fila para leer su observación. Doble clic abre el comprobante.")
        self.lbl_observacion.pack(anchor="w", pady=(8, 0))

    def refrescar(self) -> None:
        self.combo_sku.opciones([
            (producto.sku, f"{producto.sku}   {producto.nombre} · {producto.linea} · T{producto.talla} · {producto.color}")
            for producto in self.controlador.listar_productos()
        ])
        if not self.motivo.get():
            self.motivo.set(self.controlador.motivos_merma()[0])
        self.tabla.delete(*self.tabla.get_children())
        mermas = list(reversed(self.controlador.listar_mermas()))
        for merma in mermas:
            fila(self.tabla, merma.folio,
                 (merma.folio, merma.fecha_texto, merma.sku, merma.cantidad, merma.motivo.etiqueta))
        unidades = sum(merma.cantidad for merma in mermas)
        registros = "registro" if len(mermas) == 1 else "registros"
        textos_unidades = "unidad" if unidades == 1 else "unidades"
        pintar_chip(self.chip_total, f"{len(mermas)} {registros} · {unidades} {textos_unidades}", "aviso")
        self._describir_sku()
        self._contar()

    def _describir_sku(self) -> None:
        texto = self.sku.get().strip()
        self.chip_stock.pack_forget()
        self._miniatura = None
        self.lbl_foto.configure(image="", text="")
        if not texto:
            self.info_sku.configure(text="Escribe o elige el SKU de la prenda dañada o perdida.",
                                    fg=COLORES["suave"])
            return
        try:
            producto = self.controlador.obtener_producto(texto)
        except ReglaNegocioError:
            parecidos = len(self.controlador.buscar_productos(texto))
            if parecidos:
                self.info_sku.configure(
                    text=f"{parecidos} prenda(s) coinciden: elige una de la lista o sigue escribiendo.",
                    fg=COLORES["suave"],
                )
            else:
                self.info_sku.configure(text="No hay prendas con ese SKU o nombre.", fg=COLORES["peligro"])
            return
        self._miniatura = cargar_miniatura(self.controlador.ruta_foto(producto.foto), 44)
        if self._miniatura:
            self.lbl_foto.configure(image=self._miniatura, width=44)
        self.info_sku.configure(text=producto.descripcion(), fg=COLORES["texto"])
        estado, tipo = chip_estado_producto(producto)
        pintar_chip(self.chip_stock, f"{estado} · stock {producto.stock}", tipo)
        self.chip_stock.pack(anchor="w", pady=(4, 0))

    def _contar(self) -> None:
        largo = len(self.observacion.get("1.0", "end").strip())
        listo = largo >= MINIMO_OBSERVACION
        self.contador.configure(
            text=f"{largo} caracteres" + ("" if listo else f" · mínimo {MINIMO_OBSERVACION}"),
            foreground=COLORES["exito"] if listo else COLORES["suave"],
        )

    def _mostrar_observacion(self) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        documento = self.controlador.obtener_documento(seleccion[0])
        self.lbl_observacion.configure(text=f"{documento.folio}: {documento.observacion}")

    def registrar(self) -> None:
        observacion = self.observacion.get("1.0", "end").strip()
        if not pedir_confirmacion(
            self.winfo_toplevel(),
            "Registrar merma",
            f"¿Dar de baja {self.cantidad.get().strip()} unidad(es) de {self.sku.get().strip().upper()}?\n\n"
            "El stock se descuenta de inmediato.",
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
            f"{merma.folio}: {producto.sku} queda con {producto.stock} unidades ({producto.estado.etiqueta}).",
        )
        self.cantidad.set("1")
        self.observacion.delete("1.0", "end")
        self.refrescar()
        self._ver_comprobante(merma.folio)

    def _abrir_seleccion(self) -> None:
        seleccion = self.tabla.selection()
        if seleccion:
            self._ver_comprobante(seleccion[0])
