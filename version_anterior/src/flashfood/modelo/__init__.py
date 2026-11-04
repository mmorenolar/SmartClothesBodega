"""Modelo de dominio. No importa Tkinter."""

from flashfood.modelo.calzado import Calzado
from flashfood.modelo.cliente import Cliente
from flashfood.modelo.detalle_traslado import DetalleTraslado
from flashfood.modelo.errores import PersistenciaError, ReglaNegocioError
from flashfood.modelo.gestion_mermas import GestionMermas
from flashfood.modelo.gestion_traslado import GestionTraslado
from flashfood.modelo.gestionable import IGestionable
from flashfood.modelo.orden_traslado import OrdenTraslado
from flashfood.modelo.pago import (
    MetodoPago,
    PagoBilletera,
    PagoEfectivo,
    PagoTarjeta,
    PagoTransferencia,
    ResultadoPago,
)
from flashfood.modelo.pantalon import Pantalon
from flashfood.modelo.pedido import DetallePedido, EstadoPedido, Pedido
from flashfood.modelo.polera import Polera
from flashfood.modelo.producto import Bebida, Comida, Producto
from flashfood.modelo.producto_bodega import ProductoBodega
from flashfood.modelo.registro_merma import RegistroMerma
from flashfood.modelo.repartidor import Repartidor
from flashfood.modelo.sistema import FlashFood
from flashfood.modelo.tipo_calzado import TipoCalzado
from flashfood.modelo.tipo_corte import TipoCorte
from flashfood.modelo.tipo_polera import TipoPolera

__all__ = [
    "Bebida",
    "Calzado",
    "Cliente",
    "Comida",
    "DetallePedido",
    "DetalleTraslado",
    "EstadoPedido",
    "FlashFood",
    "GestionMermas",
    "GestionTraslado",
    "IGestionable",
    "MetodoPago",
    "OrdenTraslado",
    "PagoBilletera",
    "PagoEfectivo",
    "PagoTarjeta",
    "PagoTransferencia",
    "Pantalon",
    "Pedido",
    "PersistenciaError",
    "Polera",
    "Producto",
    "ProductoBodega",
    "RegistroMerma",
    "ReglaNegocioError",
    "Repartidor",
    "ResultadoPago",
    "TipoCalzado",
    "TipoCorte",
    "TipoPolera",
]
