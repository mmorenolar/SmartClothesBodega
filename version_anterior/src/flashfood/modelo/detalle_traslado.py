"""Clase DetalleTraslado para el sistema SmartClothesBodega."""
from flashfood.modelo.producto_bodega import ProductoBodega


class DetalleTraslado:
    """Encapsula la relación entre un producto y la cantidad a trasladar."""

    def __init__(self, producto: ProductoBodega, cantidad: int):
        self._producto = producto
        self._cantidad = cantidad

    @property
    def producto(self) -> ProductoBodega:
        return self._producto

    @property
    def cantidad(self) -> int:
        return self._cantidad

    def get_producto(self) -> ProductoBodega:
        return self._producto

    def get_cantidad(self) -> int:
        return self._cantidad
