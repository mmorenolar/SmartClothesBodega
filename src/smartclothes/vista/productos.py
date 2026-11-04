"""Alta, edición, ingreso de stock y consulta de pantalones, calzado y poleras."""

import tkinter as tk
from tkinter import filedialog, ttk

from smartclothes.vista.comun import (
    Pantalla,
    cargar_miniatura,
    crear_tabla,
    informar,
    mostrar_error,
    pedir_confirmacion,
    titulo,
)


class Productos(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._sku: str | None = None
        self._miniaturas: dict[str, tk.PhotoImage] = {}
        self._vista_previa: tk.PhotoImage | None = None
        titulo(self, "Productos")
        ttk.Label(
            self,
            text="Selecciona una fila para editarla. El stock solo cambia con un ingreso, un traslado o una merma.",
        ).pack(anchor="w", pady=(0, 8))

        superior = ttk.Frame(self)
        superior.pack(fill="x")
        formulario = ttk.LabelFrame(superior, text="Datos de la prenda", padding=12)
        formulario.pack(side="left", fill="both", expand=True)

        self.tipo = tk.StringVar(value="Polera")
        self.sku = tk.StringVar()
        self.nombre = tk.StringVar()
        self.talla = tk.StringVar()
        self.color = tk.StringVar()
        self.extra = tk.StringVar()
        self.foto = tk.StringVar()
        self.stock = tk.StringVar(value="0")

        ttk.Label(formulario, text="Tipo").grid(row=0, column=0, sticky="w", pady=4)
        self.tipo_combo = ttk.Combobox(
            formulario, textvariable=self.tipo, values=controlador.tipos_producto(), state="readonly", width=14
        )
        self.tipo_combo.grid(row=0, column=1, sticky="ew", padx=(8, 16), pady=4)
        self.tipo_combo.bind("<<ComboboxSelected>>", lambda _evento: self._actualizar_tipo())

        ttk.Label(formulario, text="SKU").grid(row=0, column=2, sticky="w", pady=4)
        self.sku_entry = ttk.Entry(formulario, textvariable=self.sku)
        self.sku_entry.grid(row=0, column=3, sticky="ew", padx=(8, 0), pady=4)

        ttk.Label(formulario, text="Nombre").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.nombre).grid(
            row=1, column=1, columnspan=3, sticky="ew", padx=(8, 0), pady=4
        )

        ttk.Label(formulario, text="Talla").grid(row=2, column=0, sticky="w", pady=4)
        self.talla_combo = ttk.Combobox(formulario, textvariable=self.talla, state="readonly", width=14)
        self.talla_combo.grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=4)
        ttk.Label(formulario, text="Color").grid(row=2, column=2, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.color).grid(row=2, column=3, sticky="ew", padx=(8, 0), pady=4)

        self.lbl_extra = ttk.Label(formulario, text="Corte")
        self.lbl_extra.grid(row=3, column=0, sticky="w", pady=4)
        self.extra_combo = ttk.Combobox(formulario, textvariable=self.extra, state="readonly", width=14)
        self.extra_combo.grid(row=3, column=1, sticky="ew", padx=(8, 16), pady=4)
        self.lbl_stock = ttk.Label(formulario, text="Stock inicial")
        self.lbl_stock.grid(row=3, column=2, sticky="w", pady=4)
        self.stock_entry = ttk.Entry(formulario, textvariable=self.stock)
        self.stock_entry.grid(row=3, column=3, sticky="ew", padx=(8, 0), pady=4)

        ttk.Label(formulario, text="Foto").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(formulario, textvariable=self.foto).grid(
            row=4, column=1, columnspan=2, sticky="ew", padx=(8, 8), pady=4
        )
        ttk.Button(formulario, text="Elegir imagen…", command=self.elegir_foto).grid(row=4, column=3, sticky="w")
        self.foto.trace_add("write", lambda *_args: self._mostrar_vista_previa())
        formulario.columnconfigure(1, weight=1)
        formulario.columnconfigure(3, weight=1)

        acciones = ttk.Frame(formulario)
        acciones.grid(row=5, column=0, columnspan=4, sticky="e", pady=(12, 0))
        self.boton_registrar = ttk.Button(acciones, text="Registrar", command=self.registrar)
        self.boton_guardar = ttk.Button(acciones, text="Guardar cambios", command=self.guardar)
        self.boton_eliminar = ttk.Button(acciones, text="Eliminar", command=self.eliminar)
        self.boton_limpiar = ttk.Button(acciones, text="Limpiar", command=self.limpiar)
        for boton in (self.boton_registrar, self.boton_guardar, self.boton_eliminar, self.boton_limpiar):
            boton.pack(side="left", padx=(0, 8))

        lateral = ttk.Frame(superior, padding=(12, 0, 0, 0))
        lateral.pack(side="left", fill="y")
        previa = ttk.LabelFrame(lateral, text="Vista previa", padding=8)
        previa.pack(fill="x")
        self.lbl_previa = ttk.Label(previa, text="Sin foto", anchor="center", width=22)
        self.lbl_previa.pack(ipady=40)

        ingreso = ttk.LabelFrame(lateral, text="Ingreso a bodega", padding=8)
        ingreso.pack(fill="x", pady=(12, 0))
        self.cantidad_ingreso = tk.StringVar(value="1")
        ttk.Label(ingreso, text="Unidades").grid(row=0, column=0, sticky="w")
        ttk.Entry(ingreso, textvariable=self.cantidad_ingreso, width=8).grid(row=0, column=1, padx=6)
        self.boton_ingresar = ttk.Button(ingreso, text="Ingresar", command=self.ingresar)
        self.boton_ingresar.grid(row=0, column=2)

        ttk.Label(
            self,
            text="Disponible = stock en bodega menos lo reservado en órdenes en borrador.",
        ).pack(anchor="w", pady=(12, 4))
        marco, self.tabla = crear_tabla(
            self,
            ("sku", "tipo", "nombre", "talla", "color", "detalle", "stock", "disponible", "estado"),
            ("SKU", "Tipo", "Nombre", "Talla", "Color", "Atributo especial", "Stock", "Disponible", "Estado"),
            (120, 80, 170, 55, 80, 120, 60, 80, 90),
            altura=5,
            con_imagen=True,
        )
        marco.pack(fill="both", expand=True)
        self.tabla.tag_configure("agotado", foreground="#a33a2b")
        self.tabla.bind("<<TreeviewSelect>>", self.al_seleccionar)
        self.limpiar()

    # ----- Formulario -----

    def _actualizar_tipo(self) -> None:
        tipo = self.tipo.get()
        tallas = list(self.controlador.tallas_de(tipo))
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
            self.lbl_extra.configure(text="(sin atributo extra)")
            self.extra.set("")
            self.extra_combo.configure(values=(), state="disabled")

    def _mostrar_vista_previa(self) -> None:
        imagen = cargar_miniatura(self.controlador.ruta_foto(self.foto.get().strip()), 150)
        self._vista_previa = imagen
        if imagen is None:
            self.lbl_previa.configure(image="", text="Sin foto\n(PNG o GIF)")
        else:
            self.lbl_previa.configure(image=imagen, text="")

    def elegir_foto(self) -> None:
        ruta = filedialog.askopenfilename(
            parent=self.winfo_toplevel(),
            title="Foto de la prenda",
            initialdir=str(self.controlador.directorio / "fotos"),
            filetypes=(("Imágenes", "*.png *.gif"), ("Todos los archivos", "*.*")),
        )
        if ruta:
            self.foto.set(self.controlador.foto_relativa(ruta))

    def refrescar(self) -> None:
        self.tabla.delete(*self.tabla.get_children())
        self._miniaturas.clear()
        for producto in self.controlador.listar_productos():
            imagen = cargar_miniatura(self.controlador.ruta_foto(producto.foto), 52)
            opciones = {"image": imagen} if imagen else {"text": "—"}
            if imagen:
                self._miniaturas[producto.sku] = imagen
            self.tabla.insert(
                "",
                "end",
                iid=producto.sku,
                values=(
                    producto.sku,
                    producto.tipo_visible,
                    producto.nombre,
                    producto.talla,
                    producto.color,
                    producto.detalle or "—",
                    producto.stock,
                    self.controlador.stock_disponible(producto.sku),
                    producto.estado.etiqueta,
                ),
                tags=() if producto.disponible else ("agotado",),
                **opciones,
            )

    def al_seleccionar(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        producto = self.controlador.obtener_producto(seleccion[0])
        self._sku = producto.sku
        self.tipo.set(producto.tipo_visible)
        self._actualizar_tipo()
        self.sku.set(producto.sku)
        self.nombre.set(producto.nombre)
        self.talla.set(producto.talla)
        self.color.set(producto.color)
        self.extra.set(getattr(producto, "corte", getattr(producto, "estilo", "")))
        self.foto.set(producto.foto)
        self.stock.set(str(producto.stock))
        self.tipo_combo.configure(state="disabled")
        self.sku_entry.configure(state="disabled")
        self.stock_entry.configure(state="disabled")
        self.lbl_stock.configure(text="Stock actual")
        self.boton_registrar.configure(state="disabled")
        self.boton_guardar.configure(state="normal")
        self.boton_eliminar.configure(state="normal")
        self.boton_ingresar.configure(state="normal")

    def limpiar(self) -> None:
        self._sku = None
        for variable in (self.sku, self.nombre, self.color, self.foto):
            variable.set("")
        self.stock.set("0")
        self.tipo.set("Polera")
        self.talla.set("")
        self.tipo_combo.configure(state="readonly")
        self.sku_entry.configure(state="normal")
        self.stock_entry.configure(state="normal")
        self.lbl_stock.configure(text="Stock inicial")
        self._actualizar_tipo()
        self.boton_registrar.configure(state="normal")
        self.boton_guardar.configure(state="disabled")
        self.boton_eliminar.configure(state="disabled")
        self.boton_ingresar.configure(state="disabled")
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
                self.extra.get(),
            )
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Producto registrado", f"{producto.sku} quedó en la bodega.")
        self.limpiar()
        self.refrescar()

    def guardar(self) -> None:
        if not self._sku:
            mostrar_error(self.winfo_toplevel(), "Selecciona un producto de la tabla para editarlo.")
            return
        ok, _producto = self.ejecutar(
            lambda: self.controlador.editar_producto(
                self._sku, self.nombre.get(), self.foto.get(), self.talla.get(), self.color.get(), self.extra.get()
            )
        )
        if not ok:
            return
        informar(self.winfo_toplevel(), "Producto actualizado", "Los cambios quedaron guardados.")
        self.limpiar()
        self.refrescar()

    def ingresar(self) -> None:
        if not self._sku:
            mostrar_error(self.winfo_toplevel(), "Selecciona el producto que recibe unidades.")
            return
        sku = self._sku
        ok, producto = self.ejecutar(lambda: self.controlador.ingresar_stock(sku, self.cantidad_ingreso.get()))
        if not ok:
            return
        informar(
            self.winfo_toplevel(),
            "Ingreso registrado",
            f"{producto.sku}: stock {producto.stock} · {producto.estado.etiqueta}.",
        )
        self.cantidad_ingreso.set("1")
        self.refrescar()
        self.tabla.selection_set(sku)
        self.al_seleccionar()

    def eliminar(self) -> None:
        if not self._sku:
            mostrar_error(self.winfo_toplevel(), "Selecciona un producto de la tabla para eliminarlo.")
            return
        if not pedir_confirmacion(self.winfo_toplevel(), "Eliminar producto", f"¿Eliminar {self._sku}?"):
            return
        ok, _resultado = self.ejecutar(lambda: self.controlador.eliminar_producto(self._sku))
        if not ok:
            return
        informar(self.winfo_toplevel(), "Producto eliminado", "El producto salió del catálogo.")
        self.limpiar()
        self.refrescar()
