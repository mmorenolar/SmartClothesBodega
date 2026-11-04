"""Clase Pantalon para el sistema SmartClothesBodega."""
from flashfood.modelo.producto_bodega import ProductoBodega
from flashfood.modelo.tipo_corte import TipoCorte


class Pantalon(ProductoBodega):
    """Subclase Pantalon que hereda de ProductoBodega."""

    def __init__(
        self,
        sku: str,
        nombre: str,
        foto: str,
        stock: int,
        talla: str,
        color: str,
        tipo_corte: TipoCorte,
    ):
        super().__init__(sku, nombre, foto, stock, talla, color)
        self._tipo_corte = tipo_corte

    @property
    def tipo_corte(self) -> TipoCorte:
        return self._tipo_corte

    @tipo_corte.setter
    def tipo_corte(self, tipo_corte: TipoCorte) -> None:
        self._tipo_corte = tipo_corte

    def get_tipo_corte(self) -> TipoCorte:
        return self._tipo_corte

    def set_tipo_corte(self, tipo_corte: TipoCorte) -> None:
        self._tipo_corte = tipo_corte

    def obtener_detalle_completo(self) -> str:
        return (
            f"PANTALON | SKU: {self.get_sku()} | Nombre: {self.get_nombre()} "
            f"| Corte: {self._tipo_corte} | Talla: {self.get_talla()} "
            f"| Color: {self.get_color()} | Stock: {self.get_stock()} | Estado: {self.get_estado()}"
        )
