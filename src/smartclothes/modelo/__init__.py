"""Modelo de dominio. No importa Tkinter."""

from smartclothes.modelo.errores import PersistenciaError, ReglaNegocioError
from smartclothes.modelo.producto import Calzado, Chaqueta, EstadoProducto, Pantalon, Polera, Producto
from smartclothes.modelo.salida import (
    DetalleTraslado,
    EstadoOrden,
    MotivoMerma,
    OrdenTraslado,
    RegistroMerma,
    SalidaBodega,
)
from smartclothes.modelo.sistema import SmartClothes
from smartclothes.modelo.tienda import Tienda

__all__ = [
    "Calzado",
    "Chaqueta",
    "DetalleTraslado",
    "EstadoOrden",
    "EstadoProducto",
    "MotivoMerma",
    "OrdenTraslado",
    "Pantalon",
    "PersistenciaError",
    "Polera",
    "Producto",
    "RegistroMerma",
    "ReglaNegocioError",
    "SalidaBodega",
    "SmartClothes",
    "Tienda",
]
