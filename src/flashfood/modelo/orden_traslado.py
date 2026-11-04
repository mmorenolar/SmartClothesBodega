"""Clase OrdenTraslado para el sistema SmartClothesBodega."""
from datetime import date
from typing import List
from flashfood.modelo.detalle_traslado import DetalleTraslado
from flashfood.modelo.producto_bodega import ProductoBodega


class OrdenTraslado:
    """Encapsula la información de una orden o comprobante de traslado."""

    _contador_folio: int = 1001

    def __init__(self, tienda_destino: str, capacidad_maxima: int = 10):
        self._folio = OrdenTraslado._contador_folio
        OrdenTraslado._contador_folio += 1
        self._fecha_despacho = date.today().isoformat()
        self._tienda_destino = tienda_destino
        self._detalles: List[DetalleTraslado] = []

    def agregar_detalle(self, producto: ProductoBodega, cantidad: int) -> None:
        self._detalles.append(DetalleTraslado(producto, cantidad))

    def emitir_comprobante(self) -> str:
        comprobante = (
            "==================================================================\n"
            f"          COMPROBANTE ORDEN DE TRASLADO N {self._folio}\n"
            "==================================================================\n"
            f"Fecha Despacho : {self._fecha_despacho}\n"
            f"Tienda Destino : {self._tienda_destino}\n"
            "------------------------------------------------------------------\n"
            "PRODUCTOS TRANSFERIDOS:\n"
        )
        for detalle in self._detalles:
            p = detalle.get_producto()
            cant = detalle.get_cantidad()
            comprobante += (
                f" - SKU: {p.get_sku()} | {p.get_nombre()} | "
                f"Talla: {p.get_talla()} | Color: {p.get_color()} | Cantidad: {cant}\n"
            )
        comprobante += "-------------------------------------------------------------------------"
        return comprobante

    def get_folio(self) -> int:
        return self._folio
