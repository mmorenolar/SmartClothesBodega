"""Clase Calzado para el sistema SmartClothesBodega."""
from flashfood.modelo.producto_bodega import ProductoBodega
from flashfood.modelo.tipo_calzado import TipoCalzado


class Calzado(ProductoBodega):
    """Subclase Calzado que hereda de ProductoBodega."""

    def __init__(
        self,
        sku: str,
        nombre: str,
        foto: str,
        stock: int,
        talla: str,
        color: str,
        tipo_calzado: TipoCalzado,
    ):
        super().__init__(sku, nombre, foto, stock, talla, color)
        self._tipo_calzado = tipo_calzado

    @property
    def tipo_calzado(self) -> TipoCalzado:
        return self._tipo_calzado

    @tipo_calzado.setter
    def tipo_calzado(self, tipo_calzado: TipoCalzado) -> None:
        self._tipo_calzado = tipo_calzado

    def get_tipo_calzado(self) -> TipoCalzado:
        return self._tipo_calzado

    def set_tipo_calzado(self, tipo_calzado: TipoCalzado) -> None:
        self._tipo_calzado = tipo_calzado

    def obtener_detalle_completo(self) -> str:
        return (
            f"CALZADO | SKU: {self.get_sku()} | Nombre: {self.get_nombre()} "
            f"| Estilo: {self._tipo_calzado} | Talla: {self.get_talla()} "
            f"| Color: {self.get_color()} | Stock: {self.get_stock()} | Estado: {self.get_estado()}"
        )
