"""Clase Polera para el sistema SmartClothesBodega."""
from flashfood.modelo.producto_bodega import ProductoBodega
from flashfood.modelo.tipo_polera import TipoPolera


class Polera(ProductoBodega):
    """Subclase Polera que hereda de ProductoBodega."""

    def __init__(
        self,
        sku: str,
        nombre: str,
        foto: str,
        stock: int,
        talla: str,
        color: str,
        tipo_polera: TipoPolera,
    ):
        super().__init__(sku, nombre, foto, stock, talla, color)
        self._tipo_polera = tipo_polera

    @property
    def tipo_polera(self) -> TipoPolera:
        return self._tipo_polera

    @tipo_polera.setter
    def tipo_polera(self, tipo_polera: TipoPolera) -> None:
        self._tipo_polera = tipo_polera

    def get_tipo_polera(self) -> TipoPolera:
        return self._tipo_polera

    def set_tipo_polera(self, tipo_polera: TipoPolera) -> None:
        self._tipo_polera = tipo_polera

    def obtener_detalle_completo(self) -> str:
        return (
            f"POLERA | SKU: {self.get_sku()} | Nombre: {self.get_nombre()} "
            f"| Tipo: {self._tipo_polera} | Talla: {self.get_talla()} "
            f"| Color: {self.get_color()} | Stock: {self.get_stock()} | Estado: {self.get_estado()}"
        )
