"""Clase GestionTraslado para el sistema SmartClothesBodega."""
from typing import List, Optional
from flashfood.modelo.orden_traslado import OrdenTraslado
from flashfood.modelo.producto_bodega import ProductoBodega


class GestionTraslado:
    """Controlador encargado de coordinar despachos hacia tiendas."""

    def crear_orden(
        self, tienda_destino: str, productos: List[ProductoBodega], cantidades: List[int]
    ) -> Optional[OrdenTraslado]:
        if len(productos) != len(cantidades):
            print("ERROR: La lista de productos y cantidades no coinciden.")
            return None

        for i in range(len(productos)):
            p = productos[i]
            cantidad_pedida = cantidades[i]

            if p is None:
                print("ERROR: Uno de los productos seleccionados no existe.")
                return None
            if p.get_estado() != "Disponible":
                print(f"ERROR: El producto {p.get_sku()} está Agotado.")
                return None
            if cantidad_pedida > p.get_stock():
                print(
                    f"ERROR: Stock insuficiente para {p.get_sku()}. Disponible: {p.get_stock()}"
                )
                return None

        orden = OrdenTraslado(tienda_destino, len(productos))
        for i in range(len(productos)):
            productos[i].descontar_stock(cantidades[i])
            orden.agregar_detalle(productos[i], cantidades[i])

        return orden
