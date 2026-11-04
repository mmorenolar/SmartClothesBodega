"""Comprobantes: listado de documentos y hoja con diseño de documento real, lista para imprimir."""

import tkinter as tk
import webbrowser
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


class Desplazable(tk.Frame):
    """Marco con barra de desplazamiento vertical para contenido largo."""

    def __init__(self, master, fondo: str):
        super().__init__(master, bg=fondo)
        self._lienzo = tk.Canvas(self, bg=fondo, highlightthickness=0)
        barra = ttk.Scrollbar(self, orient="vertical", command=self._lienzo.yview)
        self._lienzo.configure(yscrollcommand=barra.set)
        self._lienzo.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.interior = tk.Frame(self._lienzo, bg=fondo)
        ventana = self._lienzo.create_window((0, 0), window=self.interior, anchor="nw")
        self.interior.bind("<Configure>", lambda _e: self._lienzo.configure(scrollregion=self._lienzo.bbox("all")))
        self._lienzo.bind("<Configure>", lambda e: self._lienzo.itemconfigure(ventana, width=e.width))
        self._lienzo.bind("<Enter>", lambda _e: self._rueda(True))
        self._lienzo.bind("<Leave>", lambda _e: self._rueda(False))

    def _rueda(self, activa: bool) -> None:
        if activa:
            self._lienzo.bind_all("<MouseWheel>", lambda e: self._lienzo.yview_scroll(-e.delta // 120, "units"))
            self._lienzo.bind_all("<Button-4>", lambda _e: self._lienzo.yview_scroll(-1, "units"))
            self._lienzo.bind_all("<Button-5>", lambda _e: self._lienzo.yview_scroll(1, "units"))
        else:
            for evento in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                self._lienzo.unbind_all(evento)

    def al_inicio(self) -> None:
        self._lienzo.yview_moveto(0)


class HojaDocumento(tk.Frame):
    """Dibuja el comprobante como un documento: encabezado, datos, tabla con fotos, total y firmas."""

    def __init__(self, master, controlador):
        super().__init__(master, bg="#ffffff", padx=28, pady=22)
        self._controlador = controlador
        self._imagenes: list = []

    def limpiar(self) -> None:
        for hijo in self.winfo_children():
            hijo.destroy()
        self._imagenes.clear()

    def texto_visible(self) -> str:
        """Todo el texto de la hoja (útil para pruebas)."""
        textos = []

        def recorrer(widget):
            for hijo in widget.winfo_children():
                if isinstance(hijo, tk.Label) and hijo.cget("text"):
                    textos.append(str(hijo.cget("text")))
                recorrer(hijo)

        recorrer(self)
        return "\n".join(textos)

    def _etiqueta(self, padre, texto, tamano=10, peso="normal", color="texto", fondo="#ffffff", **opciones):
        return tk.Label(padre, text=texto, bg=fondo, fg=COLORES.get(color, color), font=tema.fuente(tamano, peso),
                        **opciones)

    def mostrar(self, datos: dict) -> None:
        self.limpiar()
        self._encabezado(datos)
        if datos["tipo"] == "traslado":
            self._datos([("Tienda destino", datos["tienda"]), ("Dirección de entrega", datos["direccion"]),
                         ("Fecha de despacho", datos["fecha"]),
                         ("Transporte", f"{datos['transporte']} · ocupado al {datos['ocupacion']}%")])
            self._tabla(datos["lineas"], "Cantidad")
            self._total(datos)
            self._firmas(("Despachado por (bodega)", "Transportista", "Recibido por (tienda)"))
        else:
            self._datos([("Fecha de registro", datos["fecha"]), ("Motivo", datos["motivo"])])
            linea = {clave: datos[clave] for clave in ("sku", "nombre", "talla", "color", "foto")}
            linea["cantidad"] = datos["unidades"]
            self._tabla([linea], "Dada de baja")
            caja = tk.Frame(self, bg=COLORES["aviso_suave"], padx=12, pady=8)
            caja.pack(fill="x", pady=(14, 0))
            tk.Frame(caja, bg=COLORES["aviso"], width=4).pack(side="left", fill="y", padx=(0, 10))
            self._etiqueta(caja, f"Observación: {datos['observacion']}", fondo=COLORES["aviso_suave"],
                           wraplength=520, justify="left").pack(side="left", anchor="w")
            self._firmas(("Responsable de bodega", "Supervisor"))
        self._etiqueta(self, f"Documento emitido por el sistema Smart Clothes · {datos['folio']}", 8,
                       color="#9aa1ac").pack(pady=(18, 0))

    def _encabezado(self, datos: dict) -> None:
        cabeza = tk.Frame(self, bg="#ffffff")
        cabeza.pack(fill="x")
        marca = tk.Frame(cabeza, bg="#ffffff")
        marca.pack(side="left")
        tk.Label(marca, text="SC", bg=COLORES["acento"], fg="#ffffff", width=3, pady=8,
                 font=tema.fuente(13, "bold")).pack(side="left")
        nombres = tk.Frame(marca, bg="#ffffff")
        nombres.pack(side="left", padx=10)
        self._etiqueta(nombres, "Smart Clothes", 14, "bold").pack(anchor="w")
        self._etiqueta(nombres, "Bodega principal · Inventario y traslados", 9, color="suave").pack(anchor="w")
        folio = tk.Frame(cabeza, bg="#ffffff", highlightthickness=2, highlightbackground=COLORES["acento"],
                         padx=16, pady=6)
        folio.pack(side="right")
        self._etiqueta(folio, datos["titulo"].upper(), 8, "bold", "acento").pack()
        self._etiqueta(folio, datos["folio"], 16, "bold").pack()
        tk.Frame(self, bg=COLORES["acento"], height=3).pack(fill="x", pady=(12, 14))

    def _datos(self, pares) -> None:
        rejilla = tk.Frame(self, bg="#ffffff")
        rejilla.pack(fill="x")
        for indice, (etiqueta, valor) in enumerate(pares):
            caja = tk.Frame(rejilla, bg=COLORES["zebra"], padx=10, pady=7)
            caja.grid(row=indice // 2, column=indice % 2, sticky="nsew", padx=(0 if indice % 2 == 0 else 10, 0),
                      pady=(0, 8))
            self._etiqueta(caja, etiqueta.upper(), 7, "bold", "suave", COLORES["zebra"]).pack(anchor="w")
            self._etiqueta(caja, valor, 10, fondo=COLORES["zebra"]).pack(anchor="w")
        rejilla.columnconfigure(0, weight=1, uniform="datos")
        rejilla.columnconfigure(1, weight=1, uniform="datos")

    def _tabla(self, lineas: list[dict], titulo_cantidad: str) -> None:
        tabla = tk.Frame(self, bg="#ffffff")
        tabla.pack(fill="x", pady=(6, 0))
        columnas = ("Foto", "SKU", "Prenda", "Talla", "Color", titulo_cantidad)
        for columna, titulo in enumerate(columnas):
            self._etiqueta(tabla, titulo.upper(), 7, "bold", "suave").grid(
                row=0, column=columna, sticky="e" if columna == 5 else "w", padx=6, pady=(0, 4))
        tk.Frame(tabla, bg=COLORES["borde"], height=2).grid(row=1, column=0, columnspan=6, sticky="ew")
        for numero, linea in enumerate(lineas):
            fila_grid = 2 + numero * 2
            imagen = cargar_miniatura(linea["foto"], 44)
            if imagen:
                self._imagenes.append(imagen)
            foto = tk.Label(tabla, bg=COLORES["zebra"], width=44 if imagen else 6, height=44 if imagen else 2,
                            image=imagen or "", text="" if imagen else "—")
            foto.grid(row=fila_grid, column=0, padx=6, pady=5, sticky="w")
            valores = (linea["sku"], linea["nombre"], linea["talla"], linea["color"], str(linea["cantidad"]))
            for columna, valor in enumerate(valores, start=1):
                ultima = columna == 5
                self._etiqueta(tabla, valor, 10, "bold" if ultima else "normal",
                               "suave" if columna == 1 else "texto").grid(
                    row=fila_grid, column=columna, sticky="e" if ultima else "w", padx=6)
            tk.Frame(tabla, bg="#eef0f3", height=1).grid(row=fila_grid + 1, column=0, columnspan=6, sticky="ew")
        tabla.columnconfigure(2, weight=1)
        tabla.columnconfigure(5, weight=1)

    def _total(self, datos: dict) -> None:
        total = tk.Frame(self, bg="#ffffff")
        total.pack(fill="x", pady=(10, 0))
        caja = tk.Frame(total, bg=COLORES["acento"], padx=14, pady=6)
        caja.pack(side="right")
        self._etiqueta(caja, "Total de unidades enviadas", 10, color="#ffffff", fondo=COLORES["acento"]).pack(
            side="left")
        self._etiqueta(caja, str(datos["unidades"]), 14, "bold", "#ffffff", COLORES["acento"]).pack(
            side="left", padx=(10, 0))
        self._etiqueta(total, f"Costo de despacho  {datos['costo']}", 10, color="suave").pack(side="right", padx=14)

    def _firmas(self, nombres: tuple[str, ...]) -> None:
        firmas = tk.Frame(self, bg="#ffffff")
        firmas.pack(fill="x", pady=(46, 0))
        for columna, nombre in enumerate(nombres):
            caja = tk.Frame(firmas, bg="#ffffff")
            caja.grid(row=0, column=columna, sticky="ew", padx=12)
            tk.Frame(caja, bg=COLORES["texto"], height=1).pack(fill="x")
            self._etiqueta(caja, nombre, 9, color="suave").pack(pady=(4, 0))
            firmas.columnconfigure(columna, weight=1, uniform="firmas")


class Comprobantes(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._pendiente: str | None = None
        self._animar = False
        self._folio: str | None = None
        encabezado(self, "Comprobantes", "Órdenes de traslado confirmadas y registros de merma.")

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.rowconfigure(0, weight=1)

        lista = Tarjeta(cuerpo, width=300, padding=14)
        lista.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        lista.pack_propagate(False)
        self.filtro = tk.StringVar(value="Todos")
        segmentos = tk.Frame(lista, bg=COLORES["tarjeta"])
        segmentos.pack(fill="x", pady=(0, 10))
        for texto in FILTROS:
            ttk.Radiobutton(segmentos, text=texto, value=texto, variable=self.filtro, style="Segmento.Toolbutton",
                            command=self.refrescar).pack(side="left", fill="x", expand=True, padx=(0, 4))
        marco, self.lista = crear_tabla(lista, ("folio", "tipo", "fecha"), ("Folio", "Tipo", "Fecha"),
                                        (90, 80, 90), altura=12)
        marco.pack(fill="both", expand=True)
        self.lista.bind("<<TreeviewSelect>>", lambda _e: self._al_elegir())

        panel = Tarjeta(cuerpo, padding=0)
        panel.grid(row=0, column=1, sticky="nsew")
        barra = tk.Frame(panel, bg=COLORES["tarjeta"], padx=18, pady=12)
        barra.pack(fill="x")
        self.boton_imprimir = ttk.Button(barra, text="Imprimir", style="Primario.TButton", command=self.imprimir)
        self.boton_imprimir.pack(side="right")
        self.boton_guardar = ttk.Button(barra, text="Guardar copia", command=self.guardar_copia)
        self.boton_guardar.pack(side="right", padx=6)
        self.lbl_documento = ttk.Label(barra, text="Comprobante", style="Seccion.TLabel")
        self.lbl_documento.pack(side="left")

        self.camion = CamionAnimado(panel)
        self.zona = Desplazable(panel, COLORES["fondo"])
        self.zona.pack(fill="both", expand=True)
        self.hoja = HojaDocumento(self.zona.interior, controlador)
        self.hoja.pack(fill="x", padx=18, pady=16)
        self.vacio = tk.Label(self.zona.interior, bg=COLORES["fondo"], fg=COLORES["suave"], font=tema.fuente(11),
                              text="Aún no hay comprobantes.\nConfirma una orden de traslado o registra una merma.")

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
        if not folio:
            self.lbl_documento.configure(text="Comprobante")
            for boton in (self.boton_imprimir, self.boton_guardar):
                boton.state(["disabled"])
            self.hoja.limpiar()
            self.hoja.pack_forget()
            self.vacio.pack(pady=80)
            return
        self.vacio.pack_forget()
        self.hoja.pack(fill="x", padx=18, pady=16)
        datos = self.controlador.datos_documento(folio)
        self.lbl_documento.configure(text=f"{datos['titulo']} · {folio}")
        for boton in (self.boton_imprimir, self.boton_guardar):
            boton.state(["!disabled"])
        if datos["tipo"] == "traslado":
            self.camion.pack(fill="x", before=self.zona)
            destino = datos["tienda"].split(" — ")[-1]
            self.camion.mostrar(f"✓  Despachado a {destino} en {datos['transporte']}", animar)
        self.hoja.mostrar(datos)
        self.zona.al_inicio()

    def imprimir(self) -> None:
        """Abre la hoja en el navegador con el cuadro de impresión (también permite guardar como PDF)."""
        if not self._folio:
            return
        ok, ruta = self.ejecutar(lambda: self.controlador.guardar_documento(self._folio, imprimir=True))
        if not ok:
            return
        webbrowser.open(ruta.as_uri())
        informar(self.winfo_toplevel(), "Listo para imprimir",
                 "Se abrió el documento. Elige la impresora o «Guardar como PDF».")

    def guardar_copia(self) -> None:
        folio = self._folio
        if not folio:
            return
        destino = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Guardar comprobante",
            initialfile=f"{folio}.html",
            defaultextension=".html",
            filetypes=(("Documento web", "*.html"),),
        )
        if not destino:
            return
        ok, ruta = self.ejecutar(lambda: self.controlador.guardar_documento(folio, destino))
        if ok:
            informar(self.winfo_toplevel(), "Comprobante guardado", f"Se guardó en {ruta}")
