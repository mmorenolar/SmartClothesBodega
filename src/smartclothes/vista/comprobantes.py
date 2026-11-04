"""Consulta y exportación de comprobantes de traslado y registros de merma."""

import tkinter as tk
from tkinter import filedialog, ttk

from smartclothes.vista.comun import Pantalla, cargar_miniatura, configurar_combo, crear_tabla, informar, titulo


class Comprobantes(Pantalla):
    def __init__(self, master, controlador):
        super().__init__(master, controlador)
        self._documentos: dict[str, str] = {}
        self._miniaturas: list[tk.PhotoImage] = []
        self._pendiente: str | None = None
        titulo(self, "Comprobantes")

        barra = ttk.Frame(self)
        barra.pack(fill="x")
        self.documento = tk.StringVar()
        self.combo = ttk.Combobox(barra, textvariable=self.documento, state="readonly")
        self.combo.pack(side="left", fill="x", expand=True)
        self.combo.bind("<<ComboboxSelected>>", lambda _evento: self.mostrar())
        self.boton_exportar = ttk.Button(barra, text="Guardar como .txt…", command=self.exportar)
        self.boton_exportar.pack(side="left", padx=(8, 0))

        self.marco_fotos = ttk.LabelFrame(self, text="Prendas transferidas", padding=8)
        marco, self.tabla = crear_tabla(
            self.marco_fotos,
            ("sku", "nombre", "talla", "color", "cantidad"),
            ("SKU", "Nombre", "Talla", "Color", "Cantidad"),
            (140, 240, 70, 110, 90),
            altura=4,
            con_imagen=True,
        )
        marco.pack(fill="both", expand=True)

        self.texto = tk.Text(self, height=18, wrap="none", font=("Courier", 11), relief="solid", borderwidth=1)
        self.texto.configure(state="disabled")

    def seleccionar(self, folio: str) -> None:
        """La pantalla de traslados o mermas pide abrir un folio recién emitido."""
        self._pendiente = folio

    def refrescar(self) -> None:
        self._documentos = {}
        etiquetas = []
        for documento in reversed(self.controlador.listar_documentos()):
            etiqueta = f"{documento.folio} — {documento.nombre_documento} — {documento.fecha_texto}"
            self._documentos[etiqueta] = documento.folio
            etiquetas.append(etiqueta)
        actual = self.documento.get()
        if self._pendiente:
            actual = next((e for e, folio in self._documentos.items() if folio == self._pendiente), actual)
            self._pendiente = None
        configurar_combo(self.combo, etiquetas, actual)
        self.mostrar()

    def mostrar(self) -> None:
        folio = self._documentos.get(self.documento.get())
        self.marco_fotos.pack_forget()
        self.texto.pack_forget()
        self.tabla.delete(*self.tabla.get_children())
        self._miniaturas.clear()
        if not folio:
            contenido = "Aún no hay comprobantes. Confirma una orden de traslado o registra una merma."
            self.boton_exportar.configure(state="disabled")
        else:
            documento = self.controlador.obtener_documento(folio)
            contenido = self.controlador.emitir_comprobante(folio)
            self.boton_exportar.configure(state="normal")
            if documento.tipo == "traslado":
                self._mostrar_fotos(documento)
        self.texto.pack(fill="both", expand=True, pady=(12, 0))
        self.texto.configure(state="normal")
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", contenido)
        self.texto.configure(state="disabled")

    def _mostrar_fotos(self, orden) -> None:
        self.marco_fotos.pack(fill="x", pady=(12, 0))
        for indice, detalle in enumerate(orden.detalles):
            imagen = cargar_miniatura(self.controlador.ruta_foto(detalle.foto), 52)
            opciones = {"image": imagen} if imagen else {"text": "—"}
            if imagen:
                self._miniaturas.append(imagen)
            self.tabla.insert(
                "",
                "end",
                iid=f"{indice}-{detalle.sku}",
                values=(detalle.sku, detalle.nombre, detalle.talla, detalle.color, detalle.cantidad),
                **opciones,
            )

    def exportar(self) -> None:
        folio = self._documentos.get(self.documento.get())
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
