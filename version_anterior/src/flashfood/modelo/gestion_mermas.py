"""Clase GestionMermas para el sistema SmartClothesBodega."""
from typing import List, Optional
from flashfood.modelo.producto_bodega import ProductoBodega
from flashfood.modelo.registro_merma import RegistroMerma


class GestionMermas:
    """Controlador de negocio para registrar pérdidas y mermas."""

    def __init__(self):
        self._historial_mermas: List[RegistroMerma] = []

    def registrar_baja(
        self, producto: Optional[ProductoBodega], cantidad: int, observacion: str
    ) -> RegistroMerma:
        if producto is None:
            raise ValueError("Error: El producto especificado no existe.")
        if cantidad <= 0:
            raise ValueError("Error: La cantidad afectada debe ser mayor a 0.")
        if cantidad > producto.get_stock():
            raise ValueError(
                f"Error: La cantidad a dar de baja ({cantidad}) supera el stock disponible ({producto.get_stock()})."
            )

        exito = producto.descontar_stock(cantidad, f"Merma: {observacion}")
        if exito:
            merma = RegistroMerma(producto.get_sku(), cantidad, observacion)
            self._historial_mermas.append(merma)
            return merma
        else:
            raise RuntimeError("Error al procesar el descuento en el stock.")

    def get_historial_mermas(self) -> List[RegistroMerma]:
        return list(self._historial_mermas)
