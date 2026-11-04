"""Órdenes de traslado en tres pasos: prendas, transporte y confirmación."""

import tkinter as tk
from datetime import date
from tkinter import ttk

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.vista import tema
from smartclothes.vista.comun import (
    COLORES,
    ComboBuscador,
    Pantalla,
    Tarjeta,
    chip,
    configurar_combo,
    crear_tabla,
    encabezado,
    etiqueta_campo,
    fila,
    informar,
    mostrar_error,
    pedir_confirmacion,
    pintar_chip,
    separador,
)

def unidades(cantidad: int) -> str:
    return f"{cantidad} unidad" if cantidad == 1 else f"{cantidad} unidades"


TIPO_ESTADO = {"Borrador": "aviso", "Confirmada": "exito", "Anulada": "neutro"}
TAG_ESTADO = {"Borrador": ("aviso",), "Confirmada": ("exito",), "Anulada": ("suave",)}


class TarjetaCamion(tk.Frame):
    """Opción de transporte que se elige con un clic. Muestra costo y ocupación."""

    def __init__(self, master, datos: dict, al_elegir):
        super().__init__(master, bg=COLORES["tarjeta"], highlightthickness=2,
                         highlightbackground=COLORES["borde"], padx=14, pady=10)
        self.nombre = datos["nombre"]
        self.apto = datos["apto"]
        fondo = COLORES["tarjeta"] if self.apto else COLORES["zebra"]
        texto = COLORES["texto"] if self.apto else COLORES["suave"]
        self.configure(bg=fondo, cursor="hand2" if self.apto else "arrow")

        cabeza = tk.Frame(self, bg=fondo)
        cabeza.pack(fill="x")
        self._radio = tk.Label(cabeza, text="○", bg=fondo, fg=COLORES["suave"], font=tema.fuente(13))
        self._radio.pack(side="left")
        tk.Label(cabeza, text=self.nombre, bg=fondo, fg=texto, font=tema.fuente(10, "bold")).pack(
            side="left", padx=(6, 0)
        )
        if datos["sugerido"]:
            chip(cabeza, "Sugerido", "acento").pack(side="right")
        tk.Label(self, text=datos["descripcion"].split(": ", 1)[-1].capitalize(), bg=fondo, fg=COLORES["suave"],
                 font=tema.fuente(9)).pack(anchor="w", pady=(2, 6))
        if self.apto:
            tk.Label(self, text=datos["costo"], bg=fondo, fg=COLORES["texto"], font=tema.fuente(16, "bold")).pack(
                anchor="w"
            )
            barra = ttk.Progressbar(self, style="Ocupacion.Horizontal.TProgressbar", maximum=100,
                                    value=max(datos["ocupacion"], 2))
            barra.pack(fill="x", pady=(6, 2))
            tk.Label(self, text=f"Camión ocupado al {datos['ocupacion']}%", bg=fondo, fg=COLORES["suave"],
                     font=tema.fuente(9)).pack(anchor="w")
        else:
            tk.Label(self, text="No sirve para esta carga", bg=fondo, fg=COLORES["peligro"],
                     font=tema.fuente(10, "bold")).pack(anchor="w")
            tk.Label(self, text=datos["motivo"].capitalize(), bg=fondo, fg=COLORES["suave"], font=tema.fuente(9),
                     wraplength=230, justify="left").pack(anchor="w", pady=(2, 0))
        if self.apto:
            self._enlazar(self, lambda _e: al_elegir(self.nombre))

    def _enlazar(self, widget, accion) -> None:
        widget.bind("<Button-1>", accion)
        for hijo in widget.winfo_children():
            self._enlazar(hijo, accion)

    def marcar(self, elegido: bool) -> None:
        self.configure(highlightbackground=COLORES["acento"] if elegido else COLORES["borde"])
        self._radio.configure(text="◉" if elegido else "○", fg=COLORES["acento"] if elegido else COLORES["suave"])


class Traslados(Pantalla):
    def __init__(self, master, controlador, ver_comprobante):
        super().__init__(master, controlador)
        self._ver_comprobante = ver_comprobante
        self._tiendas: dict[str, str] = {}
        self._folio: str | None = None
        self._tarjetas_camion: list[TarjetaCamion] = []
        encabezado(self, "Órdenes de traslado", "Envía prendas de la bodega a una tienda en tres pasos.")

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)
        self._crear_lista(cuerpo)
        self._crear_detalle(cuerpo)

    # ----- Columna izquierda: nueva orden y listado -----

    def _crear_lista(self, cuerpo) -> None:
        izquierda = Tarjeta(cuerpo, width=330)
        izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        izquierda.pack_propagate(False)
        ttk.Label(izquierda, text="Nueva orden", style="Seccion.TLabel").pack(anchor="w")
        self.tienda = tk.StringVar()
        self.fecha = tk.StringVar(value=date.today().strftime("%d-%m-%Y"))
        etiqueta_campo(izquierda, "Tienda destino").pack(anchor="w", pady=(10, 2))
        self.combo_tienda = ttk.Combobox(izquierda, textvariable=self.tienda, state="readonly")
        self.combo_tienda.pack(fill="x")
        etiqueta_campo(izquierda, "Fecha de despacho (dd-mm-aaaa)").pack(anchor="w", pady=(8, 2))
        fecha = tk.Frame(izquierda, bg=COLORES["tarjeta"])
        fecha.pack(fill="x")
        ttk.Entry(fecha, textvariable=self.fecha, width=14).pack(side="left")
        ttk.Button(fecha, text="Crear orden", style="Primario.TButton", command=self.crear).pack(side="right")
        separador(izquierda, pady=(16, 12))
        ttk.Label(izquierda, text="Órdenes", style="Seccion.TLabel").pack(anchor="w", pady=(0, 6))
        marco, self.tabla = crear_tabla(
            izquierda, ("folio", "tienda", "estado"), ("Folio", "Tienda", "Estado"), (88, 92, 92), altura=8
        )
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

    # ----- Columna derecha: detalle de la orden -----

    def _crear_detalle(self, cuerpo) -> None:
        self.panel = Tarjeta(cuerpo, padding=20)
        self.panel.grid(row=0, column=1, sticky="nsew")

        self.vacio = tk.Frame(self.panel, bg=COLORES["tarjeta"])
        tk.Label(self.vacio, text="⇄", bg=COLORES["tarjeta"], fg=COLORES["borde"], font=tema.fuente(48)).pack(
            pady=(80, 4)
        )
        tk.Label(self.vacio, text="Ninguna orden seleccionada", bg=COLORES["tarjeta"],
                 font=tema.fuente(13, "bold")).pack()
        tk.Label(self.vacio, text="Crea una orden a la izquierda o elige una del listado.", bg=COLORES["tarjeta"],
                 fg=COLORES["suave"]).pack(pady=(4, 0))

        self.detalle = tk.Frame(self.panel, bg=COLORES["tarjeta"])
        cabeza = tk.Frame(self.detalle, bg=COLORES["tarjeta"])
        cabeza.pack(fill="x")
        self.lbl_folio = ttk.Label(cabeza, style="Grande.TLabel")
        self.lbl_folio.pack(side="left")
        self.chip_estado = chip(cabeza, "", "neutro")
        self.chip_estado.pack(side="left", padx=10)
        self.boton_anular = ttk.Button(cabeza, text="Anular orden", style="Peligro.TButton", command=self.anular)
        self.boton_anular.pack(side="right")
        self.lbl_destino = ttk.Label(self.detalle, style="Ayuda.TLabel")
        self.lbl_destino.pack(anchor="w", pady=(2, 10))

        self.pasos = tk.Frame(self.detalle, bg=COLORES["tarjeta"])
        self.pasos.pack(fill="x", pady=(0, 12))
        self._etiquetas_paso = []
        for indice, texto in enumerate(("Prendas", "Transporte", "Confirmar"), start=1):
            numero = tk.Label(self.pasos, text=str(indice), width=2, font=tema.fuente(9, "bold"))
            numero.pack(side="left")
            nombre = tk.Label(self.pasos, text=texto, bg=COLORES["tarjeta"], font=tema.fuente(10, "bold"))
            nombre.pack(side="left", padx=(6, 0))
            if indice < 3:
                tk.Frame(self.pasos, bg=COLORES["borde"], height=2, width=60).pack(side="left", padx=12)
            self._etiquetas_paso.append((numero, nombre))

        # Paso 1: prendas
        self.zona_agregar = tk.Frame(self.detalle, bg=COLORES["tarjeta"])
        self.zona_agregar.pack(fill="x")
        self.sku = tk.StringVar()
        self.cantidad = tk.StringVar(value="1")
        etiqueta_campo(self.zona_agregar, "SKU de la prenda").grid(row=0, column=0, sticky="w")
        etiqueta_campo(self.zona_agregar, "Cantidad").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.combo_sku = ComboBuscador(self.zona_agregar, textvariable=self.sku, width=22)
        self.combo_sku.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.combo_sku.bind("<<ComboboxSelected>>", lambda _e: self._describir_sku())
        self.combo_sku.bind("<KeyRelease>", lambda _e: self._describir_sku(), add="+")
        self.combo_sku.bind("<Return>", lambda _e: self.agregar())
        self.entrada_cantidad = ttk.Spinbox(self.zona_agregar, from_=1, to=9999, textvariable=self.cantidad, width=7)
        self.entrada_cantidad.grid(row=1, column=1, padx=(10, 0), pady=(2, 0))
        self.entrada_cantidad.bind("<Return>", lambda _e: self.agregar())
        self.boton_agregar = ttk.Button(self.zona_agregar, text="+ Agregar", command=self.agregar)
        self.boton_agregar.grid(row=1, column=2, padx=(10, 0), pady=(2, 0))
        self.info_sku = ttk.Label(self.zona_agregar, style="Ayuda.TLabel")
        self.info_sku.grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))

        marco, self.lineas = crear_tabla(
            self.detalle,
            ("sku", "nombre", "talla", "color", "cantidad"),
            ("SKU", "Prenda", "Talla", "Color", "Cantidad"),
            (130, 170, 55, 90, 75),
            altura=4,
        )
        marco.pack(fill="both", expand=True, pady=(8, 0))
        pie_lineas = tk.Frame(self.detalle, bg=COLORES["tarjeta"])
        pie_lineas.pack(fill="x")
        self.boton_quitar = ttk.Button(pie_lineas, text="Quitar la línea seleccionada", style="Enlace.TButton",
                                       command=self.quitar)
        self.boton_quitar.pack(side="left", pady=(4, 0))
        self.lbl_unidades = ttk.Label(pie_lineas, style="Ayuda.TLabel")
        self.lbl_unidades.pack(side="right", pady=(4, 0))

        # Paso 2: transporte
        ttk.Label(self.detalle, text="Transporte", style="Seccion.TLabel").pack(anchor="w", pady=(12, 6))
        self.transporte = tk.StringVar()
        self.zona_camiones = tk.Frame(self.detalle, bg=COLORES["tarjeta"])
        self.zona_camiones.pack(fill="x")

        # Paso 3: confirmar
        pie = tk.Frame(self.detalle, bg=COLORES["tarjeta"])
        pie.pack(fill="x", pady=(14, 0))
        self.totales = ttk.Label(pie, style="Tarjeta.TLabel")
        self.totales.pack(side="left")
        self.boton_confirmar = ttk.Button(pie, text="Confirmar traslado  ›", style="Primario.TButton",
                                          command=self.confirmar)
        self.boton_confirmar.pack(side="right")
        self.boton_comprobante = ttk.Button(pie, text="Ver comprobante  ›", style="Primario.TButton",
                                            command=lambda: self._ver_comprobante(self._folio))

    # ----- Datos -----

    def refrescar(self) -> None:
        self._tiendas = {tienda.identificacion: tienda.codigo for tienda in self.controlador.listar_tiendas()}
        configurar_combo(self.combo_tienda, list(self._tiendas), self.tienda.get())
        self.combo_sku.opciones([
            (producto.sku, f"{producto.sku}   {producto.nombre} · {producto.linea} · T{producto.talla} · {producto.color}")
            for producto in self.controlador.listar_productos()
        ])

        seleccionado = self._folio
        self.tabla.delete(*self.tabla.get_children())
        for orden in reversed(self.controlador.listar_ordenes()):
            tienda = self.controlador.nombre_tienda(orden.tienda_codigo).split(" — ")[0]
            etiqueta = orden.estado.etiqueta
            fila(self.tabla, orden.folio, (orden.folio, tienda, etiqueta), tags=TAG_ESTADO.get(etiqueta, ()))
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
            self.info_sku.configure(text="Escribe o elige un SKU. Enter para agregar.", foreground=COLORES["suave"])
            return
        try:
            producto = self.controlador.obtener_producto(texto)
        except ReglaNegocioError:
            parecidos = len(self.controlador.buscar_productos(texto))
            if parecidos:
                self.info_sku.configure(
                    text=f"{parecidos} prenda(s) coinciden: elige una de la lista o sigue escribiendo.",
                    foreground=COLORES["suave"],
                )
            else:
                self.info_sku.configure(text="No hay prendas con ese SKU o nombre.", foreground=COLORES["peligro"])
            return
        disponible = self.controlador.stock_disponible(producto.sku)
        self.info_sku.configure(
            text=f"{producto.descripcion()}  ·  Disponible para traslado: {disponible}",
            foreground=COLORES["peligro"] if disponible == 0 else COLORES["suave"],
        )

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        nuevo = seleccion[0] if seleccion else None
        if nuevo != self._folio:
            self.transporte.set("")
        self._folio = nuevo
        self._mostrar(self._folio)

    def _mostrar(self, folio: str | None) -> None:
        if not folio:
            self.detalle.pack_forget()
            self.vacio.pack(fill="both", expand=True)
            return
        self.vacio.pack_forget()
        self.detalle.pack(fill="both", expand=True)
        orden = self.controlador.obtener_orden(folio)
        acciones = self.controlador.acciones(folio)
        estado = orden.estado.etiqueta

        self.lbl_folio.configure(text=f"Orden {orden.folio}")
        pintar_chip(self.chip_estado, estado, TIPO_ESTADO.get(estado, "neutro"))
        self.lbl_destino.configure(
            text=f"Para {self.controlador.nombre_tienda(orden.tienda_codigo)}  ·  Despacho {orden.fecha_texto}"
        )

        self.lineas.delete(*self.lineas.get_children())
        for detalle in orden.detalles:
            fila(self.lineas, detalle.sku, (detalle.sku, detalle.nombre, detalle.talla, detalle.color, detalle.cantidad))
        lineas = len(orden.detalles)
        self.lbl_unidades.configure(text=f"{lineas} línea{'s' if lineas != 1 else ''} · {unidades(orden.unidades)}")

        editable = acciones["puede_editar_items"]
        for widget in (self.combo_sku, self.entrada_cantidad, self.boton_agregar, self.boton_quitar):
            widget.state(["!disabled"] if editable else ["disabled"])
        self.boton_anular.state(["!disabled"] if acciones["puede_anular"] else ["disabled"])

        self._mostrar_camiones(orden)
        self._mostrar_pie(orden, acciones)

    def _mostrar_camiones(self, orden) -> None:
        for tarjeta in self._tarjetas_camion:
            tarjeta.destroy()
        self._tarjetas_camion = []
        for hijo in self.zona_camiones.winfo_children():
            hijo.destroy()
        if orden.aplicada and orden.despacho is not None:
            self.transporte.set(orden.despacho.nombre)
            tk.Label(self.zona_camiones, text=f"✓  {orden.despacho.resumen()}", bg=COLORES["exito_suave"],
                     fg=COLORES["exito"], font=tema.fuente(10, "bold"), padx=12, pady=8, anchor="w").pack(fill="x")
            return
        if not orden.detalles or orden.estado.etiqueta == "Anulada":
            self.transporte.set("")
            texto = "Esta orden fue anulada." if orden.estado.etiqueta == "Anulada" else (
                "Agrega prendas para ver qué camión conviene.")
            tk.Label(self.zona_camiones, text=texto, bg=COLORES["zebra"], fg=COLORES["suave"], padx=12, pady=10,
                     anchor="w").pack(fill="x")
            return
        cotizaciones = self.controlador.cotizar_despachos(orden.folio)
        nombres_aptos = [datos["nombre"] for datos in cotizaciones if datos["apto"]]
        if self.transporte.get() not in nombres_aptos:
            self.transporte.set(self.controlador.transporte_sugerido(orden.folio))
        for columna, datos in enumerate(cotizaciones):
            tarjeta = TarjetaCamion(self.zona_camiones, datos, self.elegir_transporte)
            tarjeta.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 12, 0))
            self.zona_camiones.columnconfigure(columna, weight=1, uniform="camion")
            self._tarjetas_camion.append(tarjeta)
        self._marcar_camiones()

    def elegir_transporte(self, nombre: str) -> None:
        self.transporte.set(nombre)
        self._marcar_camiones()
        if self._folio:
            self._mostrar_pie(self.controlador.obtener_orden(self._folio), self.controlador.acciones(self._folio))

    def _marcar_camiones(self) -> None:
        for tarjeta in self._tarjetas_camion:
            tarjeta.marcar(tarjeta.nombre == self.transporte.get())

    def _mostrar_pie(self, orden, acciones) -> None:
        confirmada = acciones["tiene_comprobante"]
        con_lineas = bool(orden.detalles)
        con_camion = bool(self.transporte.get())
        self._pintar_pasos((con_lineas or confirmada, (con_lineas and con_camion) or confirmada, confirmada))
        if confirmada:
            self.boton_confirmar.pack_forget()
            self.boton_comprobante.pack(side="right")
            self.totales.configure(text=f"Despachada · {unidades(orden.unidades)}", foreground=COLORES["exito"])
            return
        self.boton_comprobante.pack_forget()
        self.boton_confirmar.pack(side="right")
        self.boton_confirmar.state(["!disabled"] if acciones["puede_confirmar"] and con_camion else ["disabled"])
        if orden.estado.etiqueta == "Anulada":
            self.totales.configure(text="Orden anulada: no sale nada de bodega.", foreground=COLORES["suave"])
        elif con_lineas:
            self.totales.configure(text=f"{unidades(orden.unidades)} con {self.transporte.get() or '—'}",
                                   foreground=COLORES["texto"])
        else:
            self.totales.configure(text="Paso 1: agrega al menos una prenda.", foreground=COLORES["suave"])

    def _pintar_pasos(self, hechos: tuple[bool, bool, bool]) -> None:
        activo = hechos.index(False) if False in hechos else None
        for indice, (numero, nombre) in enumerate(self._etiquetas_paso):
            if hechos[indice]:
                numero.configure(text="✓", bg=COLORES["exito"], fg="#ffffff")
                nombre.configure(fg=COLORES["texto"])
            elif indice == activo:
                numero.configure(text=str(indice + 1), bg=COLORES["acento"], fg="#ffffff")
                nombre.configure(fg=COLORES["acento"])
            else:
                numero.configure(text=str(indice + 1), bg=COLORES["borde"], fg=COLORES["suave"])
                nombre.configure(fg=COLORES["suave"])

    # ----- Acciones -----

    def crear(self) -> None:
        codigo = self._tiendas.get(self.tienda.get(), "")
        ok, orden = self.ejecutar(lambda: self.controlador.crear_orden(codigo, self.fecha.get()))
        if not ok:
            return
        self._folio = orden.folio
        self.transporte.set("")
        informar(self.winfo_toplevel(), "Orden creada", f"{orden.folio} está en borrador. Agrega las prendas.")
        self.refrescar()
        self.combo_sku.focus_set()

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
        self.sku.set("")
        self.refrescar()
        self.combo_sku.focus_set()

    def quitar(self) -> None:
        if not self._folio:
            mostrar_error(self.winfo_toplevel(), "Selecciona una orden.")
            return
        seleccion = self.lineas.selection()
        if not seleccion:
            mostrar_error(self.winfo_toplevel(), "Selecciona en la tabla la línea que quieres quitar.")
            return
        ok, _orden = self.ejecutar(lambda: self.controlador.quitar_de_orden(self._folio, seleccion[0]))
        if ok:
            self.refrescar()

    def confirmar(self) -> None:
        if not self._folio:
            mostrar_error(self.winfo_toplevel(), "Selecciona una orden.")
            return
        folio = self._folio
        transporte = self.transporte.get()
        if not pedir_confirmacion(
            self.winfo_toplevel(),
            "Confirmar traslado",
            f"¿Confirmar la orden {folio} con {transporte or 'el transporte elegido'}?\n\n"
            "Las unidades se descuentan de la bodega y no se puede deshacer.",
        ):
            return
        ok, _comprobante = self.ejecutar(lambda: self.controlador.confirmar_orden(folio, transporte))
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
