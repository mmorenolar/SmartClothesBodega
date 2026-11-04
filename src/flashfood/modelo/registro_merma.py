"""Clase RegistroMerma para el sistema SmartClothesBodega."""
from datetime import datetime


class RegistroMerma:
    """Registro individual de baja o pérdida de un producto."""

    _contador_id: int = 1

    def __init__(self, sku_producto: str, cantidad_afectada: int, observacion_justificativa: str):
        self._id_merma = RegistroMerma._contador_id
        RegistroMerma._contador_id += 1
        self._sku_producto = sku_producto
        self._cantidad_afectada = cantidad_afectada
        self._observacion_justificativa = observacion_justificativa
        self._fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_id_merma(self) -> int:
        return self._id_merma

    def get_sku_producto(self) -> str:
        return self._sku_producto

    def get_cantidad_afectada(self) -> int:
        return self._cantidad_afectada

    def get_observacion_justificativa(self) -> str:
        return self._observacion_justificativa

    def get_fecha_hora(self) -> str:
        return self._fecha_hora

    def obtener_comprobante(self) -> str:
        return (
            "====================================================================\n"
            f"          REGISTRO DE MERMA N {self._id_merma}\n"
            "====================================================================\n"
            f"Fecha/Hora: {self._fecha_hora}\n"
            f"SKU Producto: {self._sku_producto}\n"
            f"Cantidad Afectada: {self._cantidad_afectada}\n"
            f"Observacion: {self._observacion_justificativa}\n"
            "---------------------------------------------------------------------"
        )
