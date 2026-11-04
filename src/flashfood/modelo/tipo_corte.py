"""Enumeración para tipos de corte de pantalón."""
from enum import Enum


class TipoCorte(Enum):
    Slim = "Slim"
    Regular = "Regular"
    Skinny = "Skinny"

    def __str__(self) -> str:
        return self.value
