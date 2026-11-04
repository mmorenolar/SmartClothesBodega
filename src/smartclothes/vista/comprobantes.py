"""Comprobantes: listado de documentos y vista tipo "hoja" con animación del camión."""

import tkinter as tk
from tkinter import filedialog, ttk

from smartclothes.vista import tema
from smartclothes.vista.comun import (
    COLORES,
    Pantalla,
    Tarjeta,
    cargar_miniatura,
    crear_tabla,
    encabezado,
    fila,
    informar,
)

FILTROS = ("Todos", "Traslados", "Mermas")


class CamionAnimado(tk.Canvas):
    """Un camión que cruza la franja de izquierda a derecha cuando sale un traslado."""

    ALTO = 84

    def __init__(self, master):
        super().__init__(master, height=self.ALTO, bg=COLORES["acento_suave"], highlightthickness=0)
        self._trabajo = None

    def _dibujar_camion(self, x: int) -> None:
        base = 64
        acento, oscuro = COLORES["acento"], COLORES["lateral"]
        self.create_rectangle(x, base - 34, x + 70, base, fill=acento, outline="", tags="camion")
        self.create_text(x + 35, base - 17, text="SC", fill="#ffffff", font=tema.fuente(10, "bold"), tags="camion")
        self.create_polygon(x + 72, base, x + 72, base - 26, x + 90, base - 26, x + 100, base - 12, x + 100, base,
                            fill=oscuro, outline="", tags="camion")
        self.create_rectangle(x + 78, base - 22, x + 90, base - 13, fill="#cfe0ff", outline="", tags="camion")
        for rueda in (x + 16, x + 54, x + 86):
            self.create_oval(rueda - 7, base - 6, rueda + 7, base + 8, fill=oscuro, outline="#ffffff", width=2,
                             tags="camion")

    def mostrar(self, texto: str, animar: bool) -> None:
        if self._trabajo:
            self.after_cancel(self._trabajo)
            self._trabajo = None
        self.delete("all")
        self.update_idletasks()
        ancho = max(self.winfo_width(), 600)
        self.create_line(0, 73, ancho, 73, fill="#c9d8fb", width=2, dash=(10, 8))
        self.create_text(18, 16, text=texto, anchor="w", fill=COLORES["acento"], font=tema.fuente(10, "bold"),
                         tags="texto")
        destino = ancho - 130
        if not animar:
            self._dibujar_camion(destino)
            return
        self._dibujar_camion(-110)
        pasos = 45
        avance_total = destino + 110

        def paso(n: int, recorrido: int = 0) -> None:
            fraccion = 1 - (1 - n / pasos) ** 2  # arranca rápido y frena al llegar
            objetivo = int(avance_total * fraccion)
            try:
                self.move("camion", objetivo - recorrido, 0)
            except tk.TclError:
                return
            if n < pasos:
                self._trabajo = self.after(18, lambda: paso(n + 1, objetivo))
            else:
                self._trabajo = None

        paso(1)


class Comprobantes(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._miniaturas: list[tk.PhotoImage] = []
        self._pendiente: str | None = None
        self._animar = False
        self._folio: str | None = None
        encabezado(self, "Comprobantes", "Órdenes de traslado confirmadas y registros de merma.")

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        lista = Tarjeta(cuerpo, width=320, padding=14)
        lista.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        lista.pack_propagate(False)
        self.filtro = tk.StringVar(value="Todos")
        segmentos = tk.Frame(lista, bg=COLORES["tarjeta"])
        segmentos.pack(fill="x", pady=(0, 10))
        for texto in FILTROS:
            ttk.Radiobutton(segmentos, text=texto, value=texto, variable=self.filtro, style="Segmento.Toolbutton",
                            command=self.refrescar).pack(side="left", fill="x", expand=True, padx=(0, 4))
        marco, self.lista = crear_tabla(lista, ("folio", "tipo", "fecha"), ("Folio", "Tipo", "Fecha"),
                                        (95, 90, 90), altura=12)
        marco.pack(fill="both", expand=True)
        self.lista.bind("<<TreeviewSelect>>", lambda _e: self._al_elegir())

        self.hoja = Tarjeta(cuerpo, padding=0)
        self.hoja.grid(row=0, column=1, sticky="nsew")
        barra = tk.Frame(self.hoja, bg=COLORES["tarjeta"], padx=18, pady=12)
        barra.pack(fill="x")
        self.boton_exportar = ttk.Button(barra, text="Guardar .txt", command=self.exportar)
        self.boton_exportar.pack(side="right")
        self.boton_copiar = ttk.Button(barra, text="Copiar", command=self.copiar)
        self.boton_copiar.pack(side="right", padx=6)
        self.lbl_documento = ttk.Label(barra, text="Comprobante", style="Seccion.TLabel")
        self.lbl_documento.pack(side="left")

        self.camion = CamionAnimado(self.hoja)

        self.marco_fotos = tk.Frame(self.hoja, bg=COLORES["tarjeta"], padx=18)
        marco_tabla, self.tabla = crear_tabla(
            self.marco_fotos,
            ("sku", "nombre", "talla", "color", "cantidad"),
            ("SKU", "Prenda", "Talla", "Color", "Cantidad"),
            (125, 170, 55, 85, 75),
            altura=3,
            con_imagen=True,
        )
        marco_tabla.pack(fill="x", pady=(10, 0))

        self.texto = tk.Text(self.hoja, wrap="none", relief="flat", bg=COLORES["tarjeta"], fg=COLORES["texto"],
                             font=tema.mono(10), padx=22, pady=14, highlightthickness=0, height=14)
        self.texto.tag_configure("titulo", font=tema.mono(11, "bold"), foreground=COLORES["acento"])
        self.texto.tag_configure("linea", foreground="#b9c0cb")
        self.texto.configure(state="disabled")

    def seleccionar(self, folio: str, animar: bool = False) -> None:
        """Traslados o mermas piden abrir un folio recién emitido."""
        self._pendiente = folio
        self._animar = animar

    def refrescar(self) -> None:
        filtro = self.filtro.get()
        documentos = list(reversed(self.controlador.listar_documentos()))
        if self._pendiente:
            filtro = "Todos"
            self.filtro.set(filtro)
        self.lista.delete(*self.lista.get_children())
        for documento in documentos:
            es_traslado = documento.tipo == "traslado"
            if (filtro == "Traslados" and not es_traslado) or (filtro == "Mermas" and es_traslado):
                continue
            fila(self.lista, documento.folio,
                 (documento.folio, "Traslado" if es_traslado else "Merma", documento.fecha_texto))
        hijos = self.lista.get_children()
        objetivo = self._pendiente or self._folio
        if objetivo not in hijos:
            objetivo = hijos[0] if hijos else None
        animar = self._animar and objetivo == self._pendiente
        self._pendiente = None
        self._animar = False
        if objetivo:
            self.lista.selection_set(objetivo)
            self.lista.see(objetivo)
        self.mostrar(objetivo, animar)

    def _al_elegir(self) -> None:
        seleccion = self.lista.selection()
        if seleccion and seleccion[0] != self._folio:
            self.mostrar(seleccion[0], animar=False)

    def mostrar(self, folio: str | None = None, animar: bool = False) -> None:
        self._folio = folio
        self.camion.pack_forget()
        self.marco_fotos.pack_forget()
        self.texto.pack_forget()
        self.tabla.delete(*self.tabla.get_children())
        self._miniaturas.clear()
        if not folio:
            contenido = "Aún no hay comprobantes.\nConfirma una orden de traslado o registra una merma."
            self.lbl_documento.configure(text="Comprobante")
            for boton in (self.boton_exportar, self.boton_copiar):
                boton.state(["disabled"])
        else:
            documento = self.controlador.obtener_documento(folio)
            contenido = self.controlador.emitir_comprobante(folio)
            tipo = "Orden de traslado" if documento.tipo == "traslado" else "Registro de merma"
            self.lbl_documento.configure(text=f"{tipo} · {folio}")
            for boton in (self.boton_exportar, self.boton_copiar):
                boton.state(["!disabled"])
            if documento.tipo == "traslado":
                self.camion.pack(fill="x")
                destino = self.controlador.nombre_tienda(documento.tienda_codigo).split(" — ")[-1]
                transporte = documento.despacho.nombre if documento.despacho else ""
                self.camion.mostrar(f"✓  Despachado a {destino} en {transporte}", animar)
                self._mostrar_fotos(documento)
        self.texto.pack(fill="both", expand=True)
        self._escribir(contenido)

    def _escribir(self, contenido: str) -> None:
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", contenido)
        for numero, linea in enumerate(contenido.splitlines(), start=1):
            if linea and set(linea) <= {"=", "-"}:
                self.texto.tag_add("linea", f"{numero}.0", f"{numero}.end")
            elif numero in (2, 3):
                self.texto.tag_add("titulo", f"{numero}.0", f"{numero}.end")
        self.texto.configure(state="disabled")

    def _mostrar_fotos(self, orden) -> None:
        self.marco_fotos.pack(fill="x")
        for indice, detalle in enumerate(orden.detalles):
            imagen = cargar_miniatura(self.controlador.ruta_foto(detalle.foto), 48)
            opciones = {"image": imagen} if imagen else {"text": "—"}
            if imagen:
                self._miniaturas.append(imagen)
            fila(self.tabla, f"{indice}-{detalle.sku}",
                 (detalle.sku, detalle.nombre, detalle.talla, detalle.color, detalle.cantidad), **opciones)
        self.tabla.configure(height=min(max(len(orden.detalles), 1), 3))

    def copiar(self) -> None:
        if not self._folio:
            return
        self.clipboard_clear()
        self.clipboard_append(self.controlador.emitir_comprobante(self._folio))
        informar(self.winfo_toplevel(), "Copiado", "El comprobante quedó en el portapapeles.")

    def exportar(self) -> None:
        folio = self._folio
        if not folio:
            return
        destino = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Guardar comprobante",
            initialfile=f"{folio}.txt",
            defaultextension=".txt",
            filetypes=(("Texto", "*.txt"),),
        )
        if not destino:
            return
        ok, ruta = self.ejecutar(lambda: self.controlador.exportar_comprobante(folio, destino))
        if ok:
            informar(self.winfo_toplevel(), "Comprobante guardado", f"Se guardó en {ruta}")
