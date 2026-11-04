"""Inicio: indicadores de la bodega, prendas que requieren atención y accesos rápidos."""

import tkinter as tk
from datetime import date
from tkinter import ttk

from smartclothes.vista import tema
from smartclothes.vista.comun import (
    COLORES,
    Pantalla,
    Tarjeta,
    al_pasar,
    animar_numero,
    chip,
    chip_estado_producto,
    encabezado,
    fecha_larga,
)


def miles(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


class Indicador(Tarjeta):
    """Tarjeta con un número grande que sube contando."""

    def __init__(self, master, titulo: str, color: str = "texto"):
        super().__init__(master, padding=18)
        self._color = color
        tk.Label(self, text=titulo.upper(), bg=COLORES["tarjeta"], fg=COLORES["suave"],
                 font=tema.fuente(8, "bold")).pack(anchor="w")
        self.valor = tk.Label(self, text="0", bg=COLORES["tarjeta"], fg=COLORES[color],
                              font=tema.fuente(24, "bold"))
        self.valor.pack(anchor="w", pady=(4, 0))
        self.detalle = tk.Label(self, text="", bg=COLORES["tarjeta"], fg=COLORES["suave"], font=tema.fuente(9))
        self.detalle.pack(anchor="w")

    def mostrar(self, valor: int, detalle: str, color: str | None = None) -> None:
        self.valor.configure(fg=COLORES[color or self._color])
        self.detalle.configure(text=detalle)
        animar_numero(self.valor, valor, miles)


class Inicio(Pantalla):
    def __init__(self, master, controlador, navegar, ver_producto):
        super().__init__(master, controlador)
        self._navegar = navegar
        self._ver_producto = ver_producto
        self._encabezado = encabezado(self, "Resumen de la bodega", fecha_larga(date.today()))

        fila_kpi = ttk.Frame(self)
        fila_kpi.pack(fill="x")
        self.kpi_productos = Indicador(fila_kpi, "Prendas registradas")
        self.kpi_unidades = Indicador(fila_kpi, "Unidades en bodega", "acento")
        self.kpi_agotados = Indicador(fila_kpi, "Prendas agotadas")
        self.kpi_ordenes = Indicador(fila_kpi, "Órdenes por confirmar")
        for columna, tarjeta in enumerate((self.kpi_productos, self.kpi_unidades, self.kpi_agotados, self.kpi_ordenes)):
            tarjeta.grid(row=0, column=columna, sticky="nsew", padx=(0 if columna == 0 else 14, 0))
            fila_kpi.columnconfigure(columna, weight=1, uniform="kpi")

        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill="both", expand=True, pady=(16, 0))
        cuerpo.columnconfigure(0, weight=3, uniform="cuerpo")
        cuerpo.columnconfigure(1, weight=2, uniform="cuerpo")
        cuerpo.rowconfigure(0, weight=1)

        atencion = Tarjeta(cuerpo)
        atencion.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        ttk.Label(atencion, text="Requieren atención", style="Seccion.TLabel").pack(anchor="w")
        ttk.Label(atencion, text="Prendas agotadas o con 10 unidades o menos.", style="Ayuda.TLabel").pack(
            anchor="w", pady=(0, 10)
        )
        self.lista_atencion = tk.Frame(atencion, bg=COLORES["tarjeta"])
        self.lista_atencion.pack(fill="both", expand=True)

        derecha = ttk.Frame(cuerpo)
        derecha.grid(row=0, column=1, sticky="nsew")
        accesos = Tarjeta(derecha)
        accesos.pack(fill="x")
        ttk.Label(accesos, text="Accesos rápidos", style="Seccion.TLabel").pack(anchor="w", pady=(0, 10))
        for texto, destino, estilo in (
            ("⇄   Nueva orden de traslado", "traslados", "Primario.TButton"),
            ("⚠   Registrar una merma", "mermas", "TButton"),
            ("▦   Agregar una prenda", "productos", "TButton"),
        ):
            ttk.Button(accesos, text=texto, style=estilo, command=lambda d=destino: self._navegar(d)).pack(
                fill="x", pady=3
            )

        movimientos = Tarjeta(derecha)
        movimientos.pack(fill="both", expand=True, pady=(14, 0))
        ttk.Label(movimientos, text="Últimos documentos", style="Seccion.TLabel").pack(anchor="w", pady=(0, 8))
        self.lista_movimientos = tk.Frame(movimientos, bg=COLORES["tarjeta"])
        self.lista_movimientos.pack(fill="both", expand=True)

        # Compatibilidad con la versión anterior: texto plano del resumen.
        self.resumen = ttk.Label(self)

    def refrescar(self) -> None:
        datos = self.controlador.resumen()
        ordenes = datos["ordenes"]
        self.kpi_productos.mostrar(datos["productos"], f"{datos['disponibles']} disponibles")
        self.kpi_unidades.mostrar(datos["unidades"], f"{datos['tiendas']} tiendas destino")
        self.kpi_agotados.mostrar(
            datos["agotados"],
            "todo con stock" if not datos["agotados"] else "revisa y repone",
            "peligro" if datos["agotados"] else "exito",
        )
        self.kpi_ordenes.mostrar(ordenes.get("Borrador", 0), f"{ordenes.get('Confirmada', 0)} confirmadas")
        self.resumen.configure(text=str(datos))
        self._llenar_atencion()
        self._llenar_movimientos()

    def _llenar_atencion(self) -> None:
        for hijo in self.lista_atencion.winfo_children():
            hijo.destroy()
        criticos = self.controlador.productos_criticos()
        if not criticos:
            tk.Label(self.lista_atencion, text="✓  Todo el stock está en buen nivel.", bg=COLORES["tarjeta"],
                     fg=COLORES["exito"], font=tema.fuente(10)).pack(anchor="w", pady=8)
            return
        for producto in criticos[:7]:
            fila = tk.Frame(self.lista_atencion, bg=COLORES["tarjeta"], cursor="hand2", pady=7)
            fila.pack(fill="x")
            nombre = tk.Label(fila, text=producto.nombre, bg=COLORES["tarjeta"], font=tema.fuente(10, "bold"))
            nombre.pack(side="left")
            detalle = tk.Label(fila, text=f"  {producto.sku} · Talla {producto.talla} · {producto.color}",
                               bg=COLORES["tarjeta"], fg=COLORES["suave"], font=tema.fuente(9))
            detalle.pack(side="left")
            texto, tipo = chip_estado_producto(producto)
            if producto.disponible:
                texto = f"{texto}: {producto.stock}"
            chip(fila, texto, tipo).pack(side="right")
            accion = tk.Label(fila, text="Reponer ›", bg=COLORES["tarjeta"], fg=COLORES["acento"],
                              font=tema.fuente(9, "bold"))
            accion.pack(side="right", padx=12)
            widgets = [fila, nombre, detalle, accion]
            al_pasar(widgets, COLORES["tarjeta"], COLORES["zebra"])
            for widget in widgets:
                widget.bind("<Button-1>", lambda _e, sku=producto.sku: self._ver_producto(sku))
            tk.Frame(self.lista_atencion, bg=COLORES["borde"], height=1).pack(fill="x")

    def _llenar_movimientos(self) -> None:
        for hijo in self.lista_movimientos.winfo_children():
            hijo.destroy()
        documentos = self.controlador.ultimos_documentos()
        if not documentos:
            tk.Label(self.lista_movimientos, text="Aún no hay traslados ni mermas.", bg=COLORES["tarjeta"],
                     fg=COLORES["suave"]).pack(anchor="w")
            return
        for documento in documentos:
            fila = tk.Frame(self.lista_movimientos, bg=COLORES["tarjeta"], pady=4)
            fila.pack(fill="x")
            es_traslado = documento.tipo == "traslado"
            tk.Label(fila, text="⇄" if es_traslado else "⚠", width=2, bg=COLORES["tarjeta"],
                     fg=COLORES["acento"] if es_traslado else COLORES["aviso"], font=tema.fuente(12)).pack(side="left")
            tk.Label(fila, text=documento.folio, bg=COLORES["tarjeta"], font=tema.fuente(10, "bold")).pack(
                side="left", padx=(4, 8)
            )
            tk.Label(fila, text=f"{documento.unidades} u. · {documento.fecha_texto}", bg=COLORES["tarjeta"],
                     fg=COLORES["suave"], font=tema.fuente(9)).pack(side="right")
