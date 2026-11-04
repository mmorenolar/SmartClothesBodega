"""Pantalla de inicio: resumen de la bodega y acceso a los módulos."""

from tkinter import ttk

from smartclothes.vista.comun import MODULOS, Pantalla, titulo

REGLAS = (
    "• Una orden de traslado solo se confirma si cada prenda está Disponible y hay stock suficiente.\n"
    "• Al confirmar, las unidades se descuentan de inmediato y se emite un comprobante con folio único.\n"
    "• Una merma descuenta el stock en el momento y deja un Registro de Merma con su propio folio.\n"
    "• Si el stock de una prenda llega a 0, su estado cambia solo a Agotado.\n"
    "• El stock y el estado no se editan a mano: solo cambian con ingresos, traslados y mermas."
)


class Inicio(Pantalla):
    def __init__(self, master, controlador, navegar):
        super().__init__(master, controlador)
        self._navegar = navegar
        titulo(self, "Bodega principal")
        ttk.Label(
            self,
            text="Control del stock físico, envíos a tiendas y bajas por daño, pérdida o falla de fábrica.",
            wraplength=780,
        ).pack(anchor="w")

        reglas = ttk.LabelFrame(self, text="Reglas de la bodega", padding=12)
        reglas.pack(fill="x", pady=12)
        ttk.Label(reglas, text=REGLAS, justify="left", wraplength=760).pack(anchor="w")

        estado = ttk.LabelFrame(self, text="Estado actual", padding=12)
        estado.pack(fill="x", pady=(0, 12))
        self.resumen = ttk.Label(estado, justify="left", style="Dato.TLabel")
        self.resumen.pack(anchor="w")

        acceso = ttk.LabelFrame(self, text="Módulos", padding=12)
        acceso.pack(fill="x")
        visibles = [(clave, etiqueta) for clave, etiqueta in MODULOS if clave != "inicio"]
        for indice, (clave, etiqueta) in enumerate(visibles):
            boton = ttk.Button(acceso, text=etiqueta, command=lambda destino=clave: self._navegar(destino))
            boton.grid(row=indice // 3, column=indice % 3, sticky="ew", padx=4, pady=4)
        for columna in range(3):
            acceso.columnconfigure(columna, weight=1)

    def refrescar(self) -> None:
        datos = self.controlador.resumen()
        ordenes = ", ".join(f"{estado} {cantidad}" for estado, cantidad in datos["ordenes"].items())
        lineas = [
            f"Productos: {datos['productos']}  (Disponibles {datos['disponibles']} · Agotados {datos['agotados']})",
            f"Unidades en bodega: {datos['unidades']}",
            f"Tiendas destino: {datos['tiendas']}",
            f"Órdenes de traslado: {ordenes}",
            f"Mermas registradas: {datos['mermas']}  ({datos['unidades_mermadas']} unidades dadas de baja)",
        ]
        self.resumen.configure(text="\n".join(lineas))
