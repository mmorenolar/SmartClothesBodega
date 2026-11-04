"""Recorrido del flujo completo sin interfaz gráfica."""

from datetime import date
from tempfile import TemporaryDirectory

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.modelo.producto import EstadoProducto
from smartclothes.modelo.salida import EstadoOrden, MotivoMerma
from smartclothes.modelo.sistema import SmartClothes
from smartclothes.modelo.transporte import CamionLiviano, CamionPesado
from smartclothes.persistencia.repositorio_json import RepositorioJSON


def main() -> None:
    with TemporaryDirectory() as carpeta:
        bodega = SmartClothes(RepositorioJSON(carpeta))
        jeans = bodega.registrar_producto("Pantalón", "PAN-SLIM-AZ-40", "Jeans Slim", "fotos/jeans.png", 6, "40", "Azul", "Slim")
        zapatilla = bodega.registrar_producto("Calzado", "CAL-DEP-BL-41", "Zapatilla Runner", "fotos/zapatilla.png", 4, "41", "Blanco", "Deportivo")
        polera = bodega.registrar_producto("Polera", "POL-BAS-NE-M", "Polera Básica", "fotos/polera.png", 3, "M", "Negro")
        tienda = bodega.registrar_tienda("T-CENTRO", "Smart Clothes Centro", "Ahumada 120, Santiago")

        orden = bodega.crear_orden(tienda.codigo, date.today())
        bodega.agregar_a_orden(orden.folio, jeans.sku, 2)
        bodega.agregar_a_orden(orden.folio, polera.sku, 3)
        try:
            bodega.agregar_a_orden(orden.folio, zapatilla.sku, 9)
            raise SystemExit("No debe aceptar más unidades que el stock")
        except ReglaNegocioError as error:
            print(f"Validación de stock: {error}")
        for transporte, plan, motivo in bodega.cotizar_despachos(orden.folio):
            print(f"{transporte.nombre}: {plan.resumen() if plan else 'no apto, ' + motivo}")
        try:
            bodega.confirmar_orden(orden.folio, CamionPesado())
            raise SystemExit("Un camión pesado no debe salir con 5 prendas")
        except ReglaNegocioError as error:
            print(f"Validación de transporte: {error}")
        print(bodega.confirmar_orden(orden.folio, CamionLiviano()))
        if orden.estado is not EstadoOrden.CONFIRMADA or jeans.stock != 4:
            raise SystemExit("La orden confirmada debe descontar el stock")
        if polera.estado is not EstadoProducto.AGOTADO:
            raise SystemExit("Una prenda con stock 0 debe quedar Agotada")
        print(f"{polera.sku} quedó {polera.estado.etiqueta}")

        merma = bodega.registrar_merma(zapatilla.sku, 1, MotivoMerma.FALLA_FABRICA, "Suela despegada al recibir")
        print(bodega.emitir_comprobante(merma.folio))
        if zapatilla.stock != 3:
            raise SystemExit("La merma debe descontar el stock")
    print("Flujo completo verificado.")


if __name__ == "__main__":
    main()
