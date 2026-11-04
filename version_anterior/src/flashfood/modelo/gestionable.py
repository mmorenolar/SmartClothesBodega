"""Interfaz para productos gestionables de bodega."""
from abc import ABC, abstractmethod


class IGestionable(ABC):
    """Interfaz que establece el contrato formal de gestión de inventario."""

    @abstractmethod
    def obtener_detalle_completo(self) -> str:
        """Devuelve la vista resumida o detallada de la prenda."""
        pass

    @abstractmethod
    def obtener_reporte_final(self) -> str:
        """Genera la presentación detallada al cierre del inventario."""
        pass

    @abstractmethod
    def descontar_stock(self, cantidad: int, motivo: str = "") -> bool:
        """Descuenta stock del producto de manera controlada."""
        pass
