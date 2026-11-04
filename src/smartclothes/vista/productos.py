"""Productos: buscador, tabla con fotos y panel lateral para crear, editar e ingresar stock."""

import tkinter as tk
from tkinter import filedialog, ttk

from smartclothes.vista import tema
from smartclothes.vista.comun import (
    COLORES,
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
    mostrar_error,
    pedir_confirmacion,
    pintar_chip,
    separador,
)



class Productos(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._sku: str | None = None
        self._miniaturas: dict[str, tk.PhotoImage] = {}
        self._vista_previa: tk.PhotoImage | None = None

        cabecera = encabezado(self, "Productos", "Prendas en bodega. Haz clic en una fila para ver su ficha.")
        ttk.Button(cabecera, text="+  Nueva prenda", style="Primario.TButton", command=self.limpiar).pack(
            side="right"
        )
        self.contador = ttk.Label(cabecera, style="Subtitulo.TLabel")
        self.contador.pack(side="right", padx=16, anchor="s")

        # ----- Barra de búsqueda y filtros -----
        barra = Tarjeta(self, padding=12)
        barra.pack(fill="x", pady=(0, 14))
        self.busqueda = tk.StringVar()
        buscador = ttk.Entry(barra, textvariable=self.busqueda, width=26)
        buscador.pack(side="left")
        self._marcador(buscador, "Buscar SKU, nombre o color…")
        self.busqueda.trace_add("write", lambda *_a: self._llenar_tabla())
        self.filtro = tk.StringVar(value="Todos")
        segmentos = tk.Frame(barra, bg=COLORES["tarjeta"])
        segmentos.pack(side="left", padx=16)
        for texto in ("Todos", *self.controlador.tipos_producto(), "Agotados"):
            ttk.Radiobutton(segmentos, text=texto, value=texto, variable=self.filtro, style="Segmento.Toolbutton",
                            command=self._llenar_tabla).pack(side="left", padx=(0, 4))
        self.filtro_linea = tk.StringVar(value="Todas las líneas")
        combo_linea = ttk.Combobox(barra, textvariable=self.filtro_linea, state="readonly", width=15,
                                   values=("Todas las líneas", *self.controlador.lineas()))
        combo_linea.pack(side="left")
        combo_linea.bind("<<ComboboxSelected>>", lambda _e: self._llenar_tabla())

        # ----- Cuerpo: tabla a la izquierda, ficha a la derecha -----
        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(0, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        tarjeta_tabla = Tarjeta(cuerpo, padding=8)
        tarjeta_tabla.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        marco, self.tabla = crear_tabla(
            tarjeta_tabla,
            ("sku", "nombre", "linea", "talla", "color", "stock", "estado"),
            ("SKU", "Prenda", "Línea", "Talla", "Color", "Stock", "Estado"),
            (126, 114, 62, 46, 56, 50, 98),
            altura=7,
            con_imagen=True,
        )
        marco.pack(fill="both", expand=True)
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)

        self._crear_panel(cuerpo)
        self.limpiar()

    # ----- Construcción del panel -----

    def _crear_panel(self, cuerpo) -> None:
        panel = Tarjeta(cuerpo, padding=18, width=340)
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_propagate(False)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=1)

        cabeza = tk.Frame(panel, bg=COLORES["tarjeta"])
        cabeza.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.lbl_panel = ttk.Label(cabeza, text="Nueva prenda", style="Seccion.TLabel")
        self.lbl_panel.pack(side="left")
        self.chip_estado = chip(cabeza, "", "neutro")

        foto = tk.Frame(panel, bg=COLORES["tarjeta"])
        foto.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 6))
        caja = tk.Frame(foto, bg=COLORES["fondo"], width=84, height=84)
        caja.pack(side="left")
        caja.pack_propagate(False)
        self.lbl_previa = tk.Label(caja, text="Sin\nfoto", bg=COLORES["fondo"], fg=COLORES["suave"],
                                   font=tema.fuente(9))
        self.lbl_previa.pack(expand=True)
        datos_foto = tk.Frame(foto, bg=COLORES["tarjeta"])
        datos_foto.pack(side="left", fill="x", expand=True, padx=(12, 0))
        etiqueta_campo(datos_foto, "Foto de la prenda").pack(anchor="w")
        self.foto = tk.StringVar()
        ttk.Entry(datos_foto, textvariable=self.foto).pack(fill="x", pady=(2, 6))
        ttk.Button(datos_foto, text="Elegir imagen…", command=self.elegir_foto).pack(anchor="w")
        self.foto.trace_add("write", lambda *_args: self._mostrar_vista_previa())

        self.tipo = tk.StringVar(value="Polera")
        etiqueta_campo(panel, "Tipo de prenda").grid(row=2, column=0, columnspan=2, sticky="w")
        tipos = tk.Frame(panel, bg=COLORES["tarjeta"])
        tipos.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(2, 6))
        self._botones_tipo = []
        for tipo in self.controlador.tipos_producto():
            boton = ttk.Radiobutton(tipos, text=tipo, value=tipo, variable=self.tipo,
                                    style="Chico.Segmento.Toolbutton", command=self._actualizar_tipo)
            boton.pack(side="left", fill="x", expand=True, padx=(0, 4))
            self._botones_tipo.append(boton)

        self.sku = tk.StringVar()
        self.nombre = tk.StringVar()
        self.talla = tk.StringVar()
        self.color = tk.StringVar()
        self.extra = tk.StringVar()
        self.stock = tk.StringVar(value="0")

        self.linea = tk.StringVar(value="Dama")
        separacion = (2, 6)

        etiqueta_campo(panel, "SKU").grid(row=4, column=0, sticky="w")
        etiqueta_campo(panel, "Línea").grid(row=4, column=1, sticky="w", padx=(8, 0))
        self.sku_entry = ttk.Entry(panel, textvariable=self.sku)
        self.sku_entry.grid(row=5, column=0, sticky="ew", pady=separacion)
        self.linea_combo = ttk.Combobox(panel, textvariable=self.linea, values=self.controlador.lineas(),
                                        state="readonly", width=10)
        self.linea_combo.grid(row=5, column=1, sticky="ew", padx=(8, 0), pady=separacion)
        self.linea_combo.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_tipo())

        etiqueta_campo(panel, "Nombre").grid(row=6, column=0, columnspan=2, sticky="w")
        ttk.Entry(panel, textvariable=self.nombre).grid(row=7, column=0, columnspan=2, sticky="ew", pady=separacion)

        etiqueta_campo(panel, "Talla").grid(row=8, column=0, sticky="w")
        etiqueta_campo(panel, "Color").grid(row=8, column=1, sticky="w", padx=(8, 0))
        self.talla_combo = ttk.Combobox(panel, textvariable=self.talla, state="readonly", width=8)
        self.talla_combo.grid(row=9, column=0, sticky="ew", pady=separacion)
        ttk.Entry(panel, textvariable=self.color).grid(row=9, column=1, sticky="ew", padx=(8, 0), pady=separacion)

        self.lbl_extra = etiqueta_campo(panel, "Corte")
        self.lbl_extra.grid(row=10, column=0, sticky="w")
        self.lbl_stock = etiqueta_campo(panel, "Stock inicial")
        self.lbl_stock.grid(row=10, column=1, sticky="w", padx=(8, 0))
        self.extra_combo = ttk.Combobox(panel, textvariable=self.extra, state="readonly", width=10)
        self.extra_combo.grid(row=11, column=0, sticky="ew", pady=separacion)
        self.stock_entry = ttk.Entry(panel, textvariable=self.stock)
        self.stock_entry.grid(row=11, column=1, sticky="ew", padx=(8, 0), pady=separacion)
        self.lbl_disponible = ttk.Label(panel, style="Ayuda.TLabel")
        self.lbl_disponible.grid(row=12, column=0, columnspan=2, sticky="w")

        acciones = tk.Frame(panel, bg=COLORES["tarjeta"])
        acciones.grid(row=13, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.boton_registrar = ttk.Button(acciones, text="Registrar prenda", style="Primario.TButton",
                                          command=self.registrar)
        self.boton_guardar = ttk.Button(acciones, text="Guardar cambios", style="Primario.TButton",
                                        command=self.guardar)
        self.boton_limpiar = ttk.Button(acciones, text="Cancelar", command=self.limpiar)
        self.boton_registrar.pack(side="left")
        self.boton_guardar.pack(side="left")
        self.boton_limpiar.pack(side="left", padx=6)

        self.zona_ingreso = tk.Frame(panel, bg=COLORES["tarjeta"])
        self.zona_ingreso.grid(row=14, column=0, columnspan=2, sticky="ew")
        separador(self.zona_ingreso, pady=(8, 6))
        etiqueta_campo(self.zona_ingreso, "Llegó mercadería: ingresar unidades a bodega").pack(anchor="w")
        linea = tk.Frame(self.zona_ingreso, bg=COLORES["tarjeta"])
        linea.pack(fill="x", pady=(4, 0))
        self.cantidad_ingreso = tk.StringVar(value="1")
        ttk.Spinbox(linea, from_=1, to=9999, textvariable=self.cantidad_ingreso, width=6).pack(side="left")
        self.boton_ingresar = ttk.Button(linea, text="Ingresar", command=self.ingresar)
        self.boton_ingresar.pack(side="left", padx=8)
        self.boton_eliminar = ttk.Button(linea, text="Eliminar", style="Peligro.TButton", command=self.eliminar)
        self.boton_eliminar.pack(side="right")

    @staticmethod
    def _marcador(entrada: ttk.Entry, texto: str) -> None:
        """Texto gris de ayuda dentro del buscador (placeholder)."""
        variable_nombre = entrada.cget("textvariable")
        etiqueta = tk.Label(entrada, text=texto, bg=COLORES["tarjeta"], fg="#9aa1ac", font=tema.fuente(10))

        def actualizar(*_args):
            if entrada.getvar(variable_nombre) or entrada.focus_get() is entrada:
                etiqueta.place_forget()
            else:
                etiqueta.place(x=8, rely=0.5, anchor="w")

        etiqueta.bind("<Button-1>", lambda _e: entrada.focus_set())
        entrada.bind("<FocusIn>", actualizar, add="+")
        entrada.bind("<FocusOut>", actualizar, add="+")
        entrada.after(50, actualizar)

    # ----- Formulario -----

    def _actualizar_tipo(self) -> None:
        tipo = self.tipo.get()
        tallas = list(self.controlador.tallas_de(tipo, self.linea.get()))
        self.talla_combo["values"] = tallas
        if self.talla.get() not in tallas:
            self.talla.set(tallas[0] if tallas else "")
        etiqueta, opciones = self.controlador.opciones_extra(tipo)
        if etiqueta:
            self.lbl_extra.configure(text=etiqueta)
            self.extra_combo.configure(values=opciones, state="readonly")
            if self.extra.get() not in opciones:
                self.extra.set(opciones[0])
        else:
            self.lbl_extra.configure(text="Sin atributo extra")
            self.extra.set("")
            self.extra_combo.configure(values=(), state="disabled")

    def _mostrar_vista_previa(self) -> None:
        imagen = cargar_miniatura(self.controlador.ruta_foto(self.foto.get().strip()), 92)
        self._vista_previa = imagen
        if imagen is None:
            self.lbl_previa.configure(image="", text="Sin\nfoto")
        else:
            self.lbl_previa.configure(image=imagen, text="")

    def elegir_foto(self) -> None:
        ruta = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title="Foto de la prenda",
            filetypes=(("Imágenes", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"), ("Todos los archivos", "*.*")),
        )
        if not ruta:
            return
        nombre = self.sku.get().strip() or self.nombre.get().strip()
        ok, relativa = self.ejecutar(lambda: self.controlador.importar_foto(ruta, nombre))
        if not ok:
            return
        self.foto.set(relativa)
        if self._sku:
            informar(self.winfo_toplevel(), "Foto lista", "Toca «Guardar cambios» para dejarla en la ficha.")

    def refrescar(self) -> None:
        self._llenar_tabla()
        if self._sku:
            self.seleccionar(self._sku)

    def _llenar_tabla(self) -> None:
        texto = self.busqueda.get()
        linea = self.filtro_linea.get()
        productos = self.controlador.buscar_productos(texto, self.filtro.get(),
                                                      "Todas" if linea.startswith("Todas") else linea)
        total = len(self.controlador.listar_productos())
        self.tabla.delete(*self.tabla.get_children())
        self._miniaturas.clear()
        for producto in productos:
            imagen = cargar_miniatura(self.controlador.ruta_foto(producto.foto), 48)
            opciones = {"image": imagen} if imagen else {"text": "—"}
            if imagen:
                self._miniaturas[producto.sku] = imagen
            estado, tipo = chip_estado_producto(producto)
            nombre = producto.nombre
            fila(
                self.tabla,
                producto.sku,
                (producto.sku, nombre, producto.linea, producto.talla, producto.color, producto.stock,
                 f"●  {estado}"),
                tags=(tipo,) if tipo != "exito" else (),
                **opciones,
            )
        self.contador.configure(text=f"Mostrando {len(productos)} de {total} prendas")
        if self._sku and self.tabla.exists(self._sku):
            self.tabla.selection_set(self._sku)

    def seleccionar(self, sku: str) -> None:
        if not self.tabla.exists(sku):
            self.busqueda.set("")
            self.filtro.set("Todos")
            self.filtro_linea.set("Todas las líneas")
            self._llenar_tabla()
        if self.tabla.exists(sku):
            self.tabla.selection_set(sku)
            self.tabla.see(sku)
            self.al_seleccionar()

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        producto = self.controlador.obtener_producto(seleccion[0])
        self._sku = producto.sku
        self.tipo.set(producto.tipo_visible)
        self.linea.set(producto.linea)
        self._actualizar_tipo()
        self.sku.set(producto.sku)
        self.nombre.set(producto.nombre)
        self.talla.set(producto.talla)
        self.color.set(producto.color)
        self.extra.set(producto.valor_especial)
        self.foto.set(producto.foto)
        self.stock.set(str(producto.stock))
        for boton in self._botones_tipo:
            boton.state(["disabled"])
        self.sku_entry.state(["disabled"])
        self.stock_entry.state(["disabled"])
        self.lbl_panel.configure(text="Ficha de la prenda")
        self.lbl_stock.configure(text="Stock actual")
        estado, tipo = chip_estado_producto(producto)
        pintar_chip(self.chip_estado, estado, tipo)
        self.chip_estado.pack(side="right")
        self.lbl_disponible.configure(
            text=f"Libre para traslado: {self.controlador.stock_disponible(producto.sku)} unidades"
        )
        self.boton_registrar.pack_forget()
        self.boton_guardar.pack(side="left", before=self.boton_limpiar)
        self.boton_ingresar.state(["!disabled"])
        self.zona_ingreso.grid()

    def limpiar(self) -> None:
        self._sku = None
        for variable in (self.sku, self.nombre, self.color, self.foto):
            variable.set("")
        self.stock.set("0")
        self.tipo.set("Polera")
        self.linea.set("Dama")
        self.talla.set("")
        for boton in self._botones_tipo:
            boton.state(["!disabled"])
        self.sku_entry.state(["!disabled"])
        self.stock_entry.state(["!disabled"])
        self.lbl_panel.configure(text="Nueva prenda")
        self.lbl_stock.configure(text="Stock inicial")
        self.lbl_disponible.configure(text="")
        self.chip_estado.pack_forget()
        self._actualizar_tipo()
        self.boton_guardar.pack_forget()
        self.boton_registrar.pack(side="left", before=self.boton_limpiar)
        self.boton_ingresar.state(["disabled"])
        self.zona_ingreso.grid_remove()
        if self.tabla.selection():
            self.tabla.selection_remove(self.tabla.selection())

    # ----- Acciones -----

    def registrar(self) -> None:
        ok, producto = self.ejecutar(
            lambda: self.controlador.registrar_producto(
                self.tipo.get(),
                self.sku.get(),
                self.nombre.get(),
                self.foto.get(),
                self.stock.get(),
                self.talla.get(),
                self.color.get(),
                self.linea.get(),
                self.extra.get(),
            )
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Prenda registrada", f"{producto.sku} quedó en la bodega.")
        self.limpiar()
        self._llenar_tabla()

    def guardar(self) -> None:
        if not self._sku:
            mostrar_error(self.winfo_toplevel(), "Selecciona una prenda de la tabla para editarla.")
            return
        ok, producto = self.ejecutar(
            lambda: self.controlador.editar_producto(
                self._sku, self.nombre.get(), self.foto.get(), self.talla.get(), self.color.get(),
                self.linea.get(), self.extra.get()
            )
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Cambios guardados", f"La ficha de {producto.sku} quedó actualizada.")
        self._llenar_tabla()
        self.seleccionar(producto.sku)

    def ingresar(self) -> None:
        if not self._sku:
            mostrar_error(self.winfo_toplevel(), "Selecciona la prenda que recibe unidades.")
            return
        sku = self._sku
        ok, producto = self.ejecutar(lambda: self.controlador.ingresar_stock(sku, self.cantidad_ingreso.get()))
        if not ok:
            return
        informar(
            self.winfo_toplevel(),
            "Ingreso registrado",
            f"{producto.sku}: ahora hay {producto.stock} unidades ({producto.estado.etiqueta}).",
        )
        self.cantidad_ingreso.set("1")
        self._llenar_tabla()
        self.seleccionar(sku)

    def eliminar(self) -> None:
        if not self._sku:
            mostrar_error(self.winfo_toplevel(), "Selecciona una prenda de la tabla para eliminarla.")
            return
        if not pedir_confirmacion(self.winfo_toplevel(), "Eliminar prenda", f"¿Eliminar {self._sku} del catálogo?"):
            return
        ok, _resultado = self.ejecutar(lambda: self.controlador.eliminar_producto(self._sku))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Prenda eliminada", "La prenda salió del catálogo.")
        self.limpiar()
        self._llenar_tabla()
