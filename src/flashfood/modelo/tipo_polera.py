"""Enumeración para tipos de polera."""
from enum import Enum


class TipoPolera(Enum):
    CUELLO_V = "CUELLO_V"
    CUELLO_REDONDO = "CUELLO_REDONDO"
    POLO = "POLO"
    SIN_MANGAS = "SIN_MANGAS"

    def __str__(self) -> str:
        return self.value
