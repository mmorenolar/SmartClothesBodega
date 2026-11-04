"""Clase abstracta Producto para el sistema SmartClothesBodega."""
from abc import abstractmethod
from flashfood.modelo.gestionable import IGestionable


class ProductoBodega(IGestionable):
    """Clase abstracta base para las prendas de vestir en bodega."""

    def __init__(
        self,
        sku: str,
        nombre: str,
        foto: str,
        stock: int,
        talla: str,
        color: str,
    ):
        self._sku = sku
        self._nombre = nombre
        self._foto = foto
        self._stock = stock
        self._talla = talla
        self._color = color
        self._estado = ""
        self._actualizar_estado()

    def _actualizar_estado(self) -> None:
        if self._stock > 0:
            self._estado = "Disponible"
        else:
            self._estado = "Agotado"

    def descontar_stock(self, cantidad: int, motivo: str = "") -> bool:
        if 0 < cantidad <= self._stock:
            self._stock -= cantidad
            self._actualizar_estado()
            return True
        return False

    @abstractmethod
    def obtener_detalle_completo(self) -> str:
        pass

    def obtener_reporte_final(self) -> str:
        alerta = (
            "[CRITICO: SIN STOCK]"
            if self._stock == 0
            else ("[ALERTA: REAPROVISIONAR]" if self._stock < 5 else "[OK]")
        )

        return (
            "+--------------------------------------------------------+\n"
            f"| PRODUCTO: {self._nombre:<25} SKU: {self._sku:<12} |\n"
            f"| Talla: {self._talla:<5} | Color: {self._color:<10} | Estado: {self._estado:<10} |\n"
            f"| Unidades Disponibles: {self._stock:<3} {alerta:<25} |\n"
            "+--------------------------------------------------------+"
        )

    # Properties
    @property
    def sku(self) -> str:
        return self._sku

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def foto(self) -> str:
        return self._foto

    @property
    def stock(self) -> int:
        return self._stock

    @property
    def talla(self) -> str:
        return self._talla

    @property
    def color(self) -> str:
        return self._color

    @property
    def estado(self) -> str:
        return self._estado

    # Metodos estilo Java
    def get_sku(self) -> str:
        return self._sku

    def get_nombre(self) -> str:
        return self._nombre

    def get_foto(self) -> str:
        return self._foto

    def get_stock(self) -> int:
        return self._stock

    def get_talla(self) -> str:
        return self._talla

    def get_color(self) -> str:
        return self._color

    def get_estado(self) -> str:
        return self._estado


Producto = ProductoBodega
