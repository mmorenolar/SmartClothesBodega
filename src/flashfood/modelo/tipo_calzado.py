"""Enumeración para tipos de calzado."""
from enum import Enum


class TipoCalzado(Enum):
    DEPORTIVO = "DEPORTIVO"
    CASUAL = "CASUAL"
    FORMAL = "FORMAL"
    URBANO = "URBANO"

    def __str__(self) -> str:
        return self.value
