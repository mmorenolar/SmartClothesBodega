"""Reglas de negocio, persistencia y separación del modelo."""

import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from smartclothes.modelo.errores import PersistenciaError, ReglaNegocioError
from smartclothes.modelo.producto import Calzado, Chaqueta, EstadoProducto, Pantalon, Polera, Producto
from smartclothes.modelo.salida import EstadoOrden, MotivoMerma, OrdenTraslado, RegistroMerma, SalidaBodega
from smartclothes.modelo.sistema import SmartClothes
from smartclothes.modelo.transporte import CamionLiviano, CamionPesado, Transporte
from smartclothes.persistencia.repositorio_json import RepositorioJSON

HOY = date.today()


class BodegaBase(unittest.TestCase):
    def setUp(self):
        self._temporal = tempfile.TemporaryDirectory()
        self.sistema = SmartClothes(RepositorioJSON(self._temporal.name))
        self.jeans = self.sistema.registrar_producto(
            "Pantalón", "PAN-SLIM-AZ-40", "Jeans Slim", "fotos/jeans.png", 10, "40", "Azul", "Dama", "Slim"
        )
        self.zapatilla = self.sistema.registrar_producto(
            "Calzado", "CAL-DEP-BL-41", "Zapatilla Runner", "fotos/zapatilla.png", 5, "41", "Blanco", "Hombre", "Deportivo"
        )
        self.polera = self.sistema.registrar_producto(
            "Polera", "POL-BAS-NE-M", "Polera Básica", "fotos/polera.png", 3, "M", "Negro", "Hombre"
        )
        self.tienda = self.sistema.registrar_tienda("T-CENTRO", "Smart Clothes Centro", "Ahumada 120")
        self.otra = self.sistema.registrar_tienda("T-PROVI", "Smart Clothes Providencia", "Providencia 2150")

    def tearDown(self):
        self._temporal.cleanup()

    def orden_con(self, *lineas: tuple[str, int]) -> OrdenTraslado:
        orden = self.sistema.crear_orden(self.tienda.codigo, HOY)
        for sku, cantidad in lineas:
            self.sistema.agregar_a_orden(orden.folio, sku, cantidad)
        return orden


class ReglasTests(BodegaBase):
    def test_traslado_completo_descuenta_y_emite_comprobante(self):
        orden = self.orden_con((self.jeans.sku, 4), (self.polera.sku, 1))
        self.assertEqual(self.jeans.stock, 10, "En borrador todavía no se descuenta")
        comprobante = self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        self.assertEqual(orden.estado, EstadoOrden.CONFIRMADA)
        self.assertEqual(self.jeans.stock, 6)
        self.assertEqual(self.polera.stock, 2)
        for dato in (orden.folio, HOY.strftime("%d-%m-%Y"), "Smart Clothes Centro", "PAN-SLIM-AZ-40",
                     "fotos/jeans.png", "Jeans Slim", "40", "Azul"):
            self.assertIn(dato, comprobante)

    def test_stock_cero_cambia_a_agotado_y_bloquea_traslados(self):
        orden = self.orden_con((self.polera.sku, 3))
        self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        self.assertEqual(self.polera.stock, 0)
        self.assertIs(self.polera.estado, EstadoProducto.AGOTADO)
        otra = self.sistema.crear_orden(self.tienda.codigo, HOY)
        with self.assertRaises(ReglaNegocioError) as contexto:
            self.sistema.agregar_a_orden(otra.folio, self.polera.sku, 1)
        self.assertIn("agotado", str(contexto.exception))
        self.sistema.ingresar_stock(self.polera.sku, 5)
        self.assertIs(self.polera.estado, EstadoProducto.DISPONIBLE)

    def test_no_traslada_mas_que_el_stock(self):
        orden = self.sistema.crear_orden(self.tienda.codigo, HOY)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.agregar_a_orden(orden.folio, self.zapatilla.sku, 6)
        self.assertEqual(self.zapatilla.stock, 5)
        self.assertEqual(orden.detalles, ())

    def test_dos_borradores_no_reservan_el_mismo_stock(self):
        self.orden_con((self.jeans.sku, 7))
        segunda = self.sistema.crear_orden(self.otra.codigo, HOY)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.agregar_a_orden(segunda.folio, self.jeans.sku, 4)
        self.sistema.agregar_a_orden(segunda.folio, self.jeans.sku, 3)
        self.assertEqual(self.sistema.stock_disponible(self.jeans.sku), 0)
        self.assertEqual(self.jeans.stock, 10)

    def test_confirmar_revalida_y_no_deja_descuentos_a_medias(self):
        orden = self.orden_con((self.jeans.sku, 2), (self.zapatilla.sku, 5))
        self.sistema.registrar_merma(self.zapatilla.sku, 1, MotivoMerma.PERDIDA, "Extraviada en el inventario")
        with self.assertRaises(ReglaNegocioError):
            self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        self.assertEqual(self.jeans.stock, 10, "El jeans no debe quedar descontado")
        self.assertEqual(orden.estado, EstadoOrden.BORRADOR)

    def test_orden_confirmada_es_final_y_no_se_confirma_dos_veces(self):
        orden = self.orden_con((self.jeans.sku, 1))
        self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        for accion in (
            lambda: self.sistema.confirmar_orden(orden.folio, CamionLiviano()),
            lambda: self.sistema.anular_orden(orden.folio),
            lambda: self.sistema.agregar_a_orden(orden.folio, self.jeans.sku, 1),
            lambda: self.sistema.quitar_de_orden(orden.folio, self.jeans.sku),
        ):
            with self.assertRaises(ReglaNegocioError):
                accion()
        self.assertEqual(self.jeans.stock, 9)

    def test_orden_vacia_no_se_confirma_y_anular_libera_reserva(self):
        vacia = self.sistema.crear_orden(self.tienda.codigo, HOY)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.confirmar_orden(vacia.folio, CamionLiviano())
        orden = self.orden_con((self.jeans.sku, 10))
        self.assertEqual(self.sistema.stock_disponible(self.jeans.sku), 0)
        self.sistema.anular_orden(orden.folio)
        self.assertEqual(orden.estado, EstadoOrden.ANULADA)
        self.assertEqual(self.sistema.stock_disponible(self.jeans.sku), 10)

    def test_fecha_de_despacho_y_tienda_validas(self):
        with self.assertRaises(ReglaNegocioError):
            self.sistema.crear_orden(self.tienda.codigo, HOY - timedelta(days=1))
        with self.assertRaises(ReglaNegocioError):
            self.sistema.crear_orden("NO-EXISTE", HOY)
        futura = self.sistema.crear_orden(self.tienda.codigo, HOY + timedelta(days=3))
        self.assertEqual(futura.fecha_despacho, HOY + timedelta(days=3))

    def test_folios_unicos_y_correlativos(self):
        primera = self.sistema.crear_orden(self.tienda.codigo, HOY)
        segunda = self.sistema.crear_orden(self.tienda.codigo, HOY)
        merma = self.sistema.registrar_merma(self.jeans.sku, 1, MotivoMerma.DANO, "Costura abierta en pierna")
        self.assertEqual((primera.folio, segunda.folio, merma.folio), ("OT-000001", "OT-000002", "ME-000001"))

    def test_merma_descuenta_agota_y_emite_registro(self):
        merma = self.sistema.registrar_merma(
            self.polera.sku, 3, MotivoMerma.FALLA_FABRICA, "Estampado defectuoso de fábrica"
        )
        self.assertEqual(self.polera.stock, 0)
        self.assertIs(self.polera.estado, EstadoProducto.AGOTADO)
        registro = self.sistema.emitir_comprobante(merma.folio)
        self.assertIn("REGISTRO DE MERMA", registro)
        self.assertIn("Falla de fábrica", registro)
        self.assertIn("Estampado defectuoso", registro)

    def test_merma_invalida_no_toca_el_stock_ni_gasta_folio(self):
        casos = (
            (self.jeans.sku, 11, MotivoMerma.DANO, "Más unidades que el stock"),
            (self.jeans.sku, 1, MotivoMerma.DANO, "corta"),
            (self.jeans.sku, 0, MotivoMerma.DANO, "Cantidad cero no vale"),
            ("NO-EXISTE", 1, MotivoMerma.DANO, "SKU que no existe"),
        )
        for sku, cantidad, motivo, observacion in casos:
            with self.assertRaises(ReglaNegocioError):
                self.sistema.registrar_merma(sku, cantidad, motivo, observacion)
        self.assertEqual(self.jeans.stock, 10)
        merma = self.sistema.registrar_merma(self.jeans.sku, 1, MotivoMerma.DANO, "Mancha que no sale")
        self.assertEqual(merma.folio, "ME-000001")

    def test_stock_y_estado_no_se_asignan_desde_afuera(self):
        for atributo in ("stock", "estado", "disponible"):
            with self.assertRaises(AttributeError):
                setattr(self.jeans, atributo, 99)
        self.assertFalse(hasattr(self.jeans, "set_stock"))
        self.assertFalse(hasattr(self.jeans, "__actualizar_estado"))
        self.sistema.editar_producto(self.jeans.sku, "Jeans Slim Fit", "fotos/jeans.png", "42", "Azul", "Dama", "Regular")
        self.assertEqual(self.jeans.stock, 10, "Editar la ficha no cambia el stock")
        self.assertEqual((self.jeans.talla, self.jeans.corte), ("42", "Regular"))

    def test_herencia_abstraccion_y_polimorfismo(self):
        with self.assertRaises(TypeError):
            Producto("X-1", "X", "x.png", 1, "M", "Rojo", "Dama")
        with self.assertRaises(TypeError):
            SalidaBodega("F-1", HOY)
        self.assertIsInstance(self.jeans, Pantalon)
        self.assertIsInstance(self.zapatilla, Calzado)
        self.assertIsInstance(self.polera, Polera)
        self.assertEqual(
            [producto.detalle for producto in (self.jeans, self.zapatilla, self.polera)],
            ["Corte Slim", "Estilo Deportivo", ""],
        )
        self.assertNotEqual(Polera.tallas_validas(), Calzado.tallas_validas())
        self.assertFalse(hasattr(self.polera, "corte") or hasattr(self.polera, "estilo"))
        orden = self.orden_con((self.jeans.sku, 1))
        self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        merma = self.sistema.registrar_merma(self.jeans.sku, 1, MotivoMerma.DANO, "Roto al desembalar")
        documentos = self.sistema.listar_documentos()
        self.assertTrue(all(isinstance(documento, SalidaBodega) for documento in documentos))
        self.assertEqual({type(documento) for documento in documentos}, {OrdenTraslado, RegistroMerma})
        self.assertEqual(merma.lineas(), ((self.jeans.sku, 1),))

    def test_linea_dama_hombre_infantil_con_sus_tallas(self):
        nino = self.sistema.registrar_producto(
            "Polera", "POL-NIN-AZ-8", "Polera Dino", "fotos/polera.png", 5, "8", "Azul", "Infantil"
        )
        zapatilla = self.sistema.registrar_producto(
            "Calzado", "CAL-NIN-RO-28", "Zapatilla Luces", "fotos/zapatilla.png", 5, "28", "Rosado", "Infantil",
            "Deportivo",
        )
        self.assertEqual((nino.linea, nino.talla), ("Infantil", "8"))
        self.assertIn("Infantil", zapatilla.descripcion())
        self.assertEqual(self.jeans.linea, "Dama")
        self.assertNotEqual(Polera.tallas_para("Infantil"), Polera.tallas_para("Dama"))
        with self.assertRaises(ReglaNegocioError):
            self.sistema.editar_producto(nino.sku, "Polera Dino", "fotos/polera.png", "8", "Azul", "Hombre")
        self.assertEqual(nino.linea, "Infantil", "Un cambio inválido no deja la ficha a medias")
        self.sistema.editar_producto(nino.sku, "Polera Dino", "fotos/polera.png", "M", "Azul", "Hombre")
        self.assertEqual((nino.linea, nino.talla), ("Hombre", "M"))

    def test_chaqueta_nueva_clase_hija_con_material(self):
        chaqueta = self.sistema.registrar_producto(
            "Chaqueta", "CHA-CUE-BU-M", "Chaqueta Cuero", "fotos/chaqueta.png", 4, "M", "Burdeo", "Dama",
            "cuero sintético",
        )
        self.assertIsInstance(chaqueta, Chaqueta)
        self.assertIsInstance(chaqueta, Producto)
        self.assertEqual((chaqueta.material, chaqueta.detalle), ("Cuero sintético", "Material cuero sintético"))
        self.sistema.editar_producto(chaqueta.sku, "Chaqueta Cuero", "fotos/chaqueta.png", "L", "Burdeo", "Dama",
                                     "Cuero")
        self.assertEqual((chaqueta.talla, chaqueta.valor_especial), ("L", "Cuero"))
        orden = self.orden_con((chaqueta.sku, 4))
        self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        self.assertIs(chaqueta.estado, EstadoProducto.AGOTADO)
        recargado = SmartClothes(RepositorioJSON(self._temporal.name)).obtener_producto(chaqueta.sku)
        self.assertEqual((type(recargado), recargado.material), (Chaqueta, "Cuero"))

    def test_validaciones_de_ficha(self):
        casos = (
            ("Polera", "POL-1", "Polera", "p.png", 1, "40", "Rojo", "Dama", None),
            ("Pantalón", "PAN-1", "Jeans", "p.png", 1, "40", "Azul", "Hombre", "Campana"),
            ("Calzado", "CAL-1", "Bota", "p.png", 1, "41", "Café", "Hombre", "Trekking"),
            ("Polera", "POL 1", "Polera", "p.png", 1, "M", "Rojo", "Dama", None),
            ("Polera", "POL-2", "Polera", "", 1, "M", "Rojo", "Dama", None),
            ("Polera", "POL-3", "Polera", "p.png", -1, "M", "Rojo", "Dama", None),
            ("Polera", "pol-bas-ne-m", "Repetida", "p.png", 1, "M", "Rojo", "Dama", None),
            ("Bufanda", "BUF-1", "Bufanda", "p.png", 1, "M", "Rojo", "Dama", None),
            ("Chaqueta", "CHA-1", "Parka", "p.png", 1, "M", "Rojo", "Dama", "Plástico"),
            ("Polera", "POL-4", "Polera", "p.png", 1, "M", "Rojo", "Mascotas", None),
            ("Polera", "POL-5", "Polera niño", "p.png", 1, "M", "Rojo", "Infantil", None),
            ("Calzado", "CAL-2", "Zapatilla niño", "p.png", 1, "41", "Azul", "Infantil", "Casual"),
        )
        for datos in casos:
            with self.assertRaises(ReglaNegocioError, msg=str(datos)):
                self.sistema.registrar_producto(*datos)
        self.assertEqual(len(self.sistema.listar_productos()), 3)

    def test_no_elimina_producto_ni_tienda_en_uso(self):
        orden = self.orden_con((self.jeans.sku, 1))
        with self.assertRaises(ReglaNegocioError):
            self.sistema.eliminar_producto(self.jeans.sku)
        with self.assertRaises(ReglaNegocioError):
            self.sistema.eliminar_tienda(self.tienda.codigo)
        self.sistema.eliminar_tienda(self.otra.codigo)
        self.sistema.anular_orden(orden.folio)
        self.sistema.eliminar_producto(self.zapatilla.sku)
        self.assertEqual(len(self.sistema.listar_productos()), 2)

    def test_comprobante_guarda_los_datos_del_momento(self):
        orden = self.orden_con((self.jeans.sku, 2))
        self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        self.sistema.editar_producto(self.jeans.sku, "Jeans Nuevo", "fotos/otra.png", "40", "Celeste", "Dama", "Slim")
        comprobante = self.sistema.emitir_comprobante(orden.folio)
        self.assertIn("Jeans Slim", comprobante)
        self.assertNotIn("Jeans Nuevo", comprobante)

    def test_acciones_siguen_al_estado(self):
        orden = self.sistema.crear_orden(self.tienda.codigo, HOY)
        self.assertFalse(self.sistema.acciones(orden.folio)["puede_confirmar"])
        self.sistema.agregar_a_orden(orden.folio, self.jeans.sku, 1)
        self.assertTrue(self.sistema.acciones(orden.folio)["puede_confirmar"])
        self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        acciones = self.sistema.acciones(orden.folio)
        self.assertFalse(acciones["puede_editar_items"] or acciones["puede_anular"])
        self.assertTrue(acciones["tiene_comprobante"])

    def test_despacho_polimorfico_liviano_y_pesado(self):
        bodega = self.sistema.registrar_producto(
            "Polera", "POL-STOCK-L", "Polera Stock", "fotos/polera.png", 1000, "L", "Gris", "Hombre"
        )
        chica = self.orden_con((self.jeans.sku, 5))
        grande = self.orden_con((bodega.sku, 400))
        with self.assertRaises(ReglaNegocioError):
            self.sistema.confirmar_orden(chica.folio, CamionPesado())
        with self.assertRaises(ReglaNegocioError):
            self.sistema.confirmar_orden(grande.folio, CamionLiviano())
        self.assertEqual((self.jeans.stock, bodega.stock), (10, 1000), "Un transporte rechazado no descuenta")
        self.assertIsInstance(self.sistema.transporte_sugerido(chica.folio), CamionLiviano)
        self.assertIsInstance(self.sistema.transporte_sugerido(grande.folio), CamionPesado)
        self.sistema.confirmar_orden(grande.folio, CamionPesado())
        self.assertEqual(grande.despacho.costo, CamionPesado.TARIFA_BASE + 400 * CamionPesado.COSTO_POR_PRENDA)
        self.assertEqual(grande.despacho.ocupacion, 13)
        self.assertIn("Camión pesado", self.sistema.emitir_comprobante(grande.folio))

    def test_cada_camion_calcula_distinto_con_el_mismo_metodo(self):
        camiones: list[Transporte] = [CamionLiviano(), CamionPesado()]
        costos = [camion.costo(250) for camion in camiones]
        self.assertNotEqual(costos[0], costos[1])
        self.assertEqual([camion.puede_transportar(250) for camion in camiones], [True, True])
        self.assertEqual([camion.puede_transportar(50) for camion in camiones], [True, False])
        self.assertEqual([camion.puede_transportar(1500) for camion in camiones], [False, True])
        with self.assertRaises(TypeError):
            Transporte()

    def test_sin_transporte_valido_no_se_confirma(self):
        orden = self.orden_con((self.jeans.sku, 1))
        with self.assertRaises(ReglaNegocioError):
            self.sistema.confirmar_orden(orden.folio, "camión")
        self.assertEqual(orden.estado, EstadoOrden.BORRADOR)
        self.assertEqual(self.jeans.stock, 10)


class PersistenciaTests(BodegaBase):
    def test_recarga_sin_volver_a_descontar(self):
        orden = self.orden_con((self.jeans.sku, 4))
        self.sistema.confirmar_orden(orden.folio, CamionLiviano())
        self.sistema.registrar_merma(self.polera.sku, 3, MotivoMerma.PERDIDA, "No aparece en el conteo")
        recuperado = SmartClothes(RepositorioJSON(self._temporal.name))
        self.assertEqual(recuperado.advertencias, ())
        self.assertEqual(recuperado.obtener_producto(self.jeans.sku).stock, 6)
        self.assertIs(recuperado.obtener_producto(self.polera.sku).estado, EstadoProducto.AGOTADO)
        self.assertEqual(recuperado.obtener_orden(orden.folio).estado, EstadoOrden.CONFIRMADA)
        self.assertEqual(recuperado.obtener_orden(orden.folio).despacho, orden.despacho)
        with self.assertRaises(ReglaNegocioError):
            recuperado.confirmar_orden(orden.folio, CamionLiviano())
        self.assertEqual(recuperado.obtener_producto(self.jeans.sku).stock, 6)
        nueva = recuperado.crear_orden(self.tienda.codigo, HOY)
        self.assertEqual(nueva.folio, "OT-000002", "El folio no se repite después de reabrir")

    def test_archivo_danado_no_cierra_y_no_se_sobrescribe(self):
        ruta = Path(self._temporal.name) / "productos.json"
        ruta.write_text("{esto no es json", encoding="utf-8")
        sistema = SmartClothes(RepositorioJSON(self._temporal.name))
        self.assertTrue(sistema.advertencias)
        self.assertEqual(sistema.listar_productos(), ())
        with self.assertRaises(PersistenciaError):
            sistema.registrar_tienda("T-NUEVA", "Nueva", "Calle 1")
        self.assertTrue(ruta.with_name("productos.json.bak").exists())

    def test_estado_manipulado_en_json_se_rechaza(self):
        ruta = Path(self._temporal.name) / "productos.json"
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos[0]["estado"] = "AGOTADO"
        ruta.write_text(json.dumps(datos), encoding="utf-8")
        sistema = SmartClothes(RepositorioJSON(self._temporal.name))
        self.assertTrue(any("no coincide" in aviso for aviso in sistema.advertencias))

    def test_datos_de_ejemplo(self):
        raiz = Path(__file__).resolve().parents[1] / "data"
        sistema = SmartClothes(RepositorioJSON(raiz))
        self.assertEqual(sistema.advertencias, ())
        self.assertEqual(sistema.obtener_producto("PAN-REG-AZ-40").detalle, "Corte Regular")
        self.assertEqual({producto.linea for producto in sistema.listar_productos()}, {"Dama", "Hombre", "Infantil"})
        self.assertIs(sistema.obtener_producto("POL-EST-RO-8").estado, EstadoProducto.AGOTADO)
        self.assertEqual(len(sistema.listar_tiendas()), 3)
        for producto in sistema.listar_productos():
            self.assertTrue((raiz / producto.foto).exists(), producto.foto)


class ControladorTests(unittest.TestCase):
    def setUp(self):
        self._temporal = tempfile.TemporaryDirectory()
        from smartclothes.controladores.controlador import Controlador

        self.controlador = Controlador(self._temporal.name)

    def tearDown(self):
        self._temporal.cleanup()

    def test_rechaza_texto_que_no_es_entero_ni_fecha(self):
        for stock in ("", "abc", "1.5", "6.000", "-5"):
            with self.assertRaises(ReglaNegocioError):
                self.controlador.registrar_producto("Polera", "POL-1", "Polera", "p.png", stock, "M", "Rojo", "Dama", "")
        self.controlador.registrar_producto("Polera", "pol-1", "Polera", "p.png", "0", "m", "Rojo", "dama", "")
        producto = self.controlador.listar_productos()[0]
        self.assertEqual((producto.sku, producto.talla, producto.estado), ("POL-1", "M", EstadoProducto.AGOTADO))
        self.controlador.registrar_tienda("t-1", "Tienda", "Calle 1")
        for fecha in ("", "2026-12-01", "31-02-2030", "mañana"):
            with self.assertRaises(ReglaNegocioError):
                self.controlador.crear_orden("T-1", fecha)
        with self.assertRaises(ReglaNegocioError):
            self.controlador.registrar_merma("POL-1", "1", "Robo", "Motivo que no existe")

    def test_documento_imprimible_con_fotos(self):
        self.controlador.registrar_tienda("T-1", "Tienda Uno", "Calle 1")
        origen = sorted((Path(__file__).resolve().parents[1] / "data" / "fotos").glob("*.png"))[0]
        foto = self.controlador.importar_foto(str(origen), "polera")
        self.controlador.registrar_producto("Polera", "POL-1", "Polera", foto, "10", "M", "Rojo", "Dama", "")
        orden = self.controlador.crear_orden("T-1", date.today().strftime("%d-%m-%Y"))
        self.controlador.agregar_a_orden(orden.folio, "POL-1", "3")
        with self.assertRaises(ReglaNegocioError):
            self.controlador.guardar_documento(orden.folio)
        self.controlador.confirmar_orden(orden.folio, "Camión 3/4 (liviano)")
        ruta = self.controlador.guardar_documento(orden.folio, Path(self._temporal.name) / "ot.html", imprimir=True)
        html = ruta.read_text(encoding="utf-8")
        for dato in (orden.folio, "Tienda Uno", "Calle 1", "POL-1", "data:image/png;base64", "window.print()"):
            self.assertIn(dato, html)

    def test_exporta_comprobante(self):
        self.controlador.registrar_producto("Calzado", "CAL-1", "Bota", "b.png", "4", "40", "Café", "Hombre", "Casual")
        merma = self.controlador.registrar_merma("CAL-1", "1", "Daño", "Caja aplastada y suela rota")
        destino = Path(self._temporal.name) / "comprobante.txt"
        self.controlador.exportar_comprobante(merma.folio, str(destino))
        self.assertIn(merma.folio, destino.read_text(encoding="utf-8"))

    def test_importa_foto_a_la_carpeta_del_proyecto(self):
        origen = sorted((Path(__file__).resolve().parents[1] / "data" / "fotos").glob("*.png"))[0]
        relativa = self.controlador.importar_foto(str(origen), "Jeans Ñandú Slim")
        self.assertTrue(relativa.startswith("fotos/jeans-nandu-slim"))
        self.assertTrue((Path(self._temporal.name) / relativa).exists())
        segunda = self.controlador.importar_foto(str(origen), "Jeans Ñandú Slim")
        self.assertNotEqual(relativa, segunda, "No debe pisar una foto existente")
        with self.assertRaises(ReglaNegocioError):
            self.controlador.importar_foto(__file__, "texto")

    def test_importa_foto_jpg_como_png(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow no está instalado")
        origen = Path(self._temporal.name) / "celular.jpg"
        Image.new("RGB", (1200, 900), (180, 40, 40)).save(origen, "JPEG")
        relativa = self.controlador.importar_foto(str(origen), "POL-ROJA-M")
        self.assertEqual(relativa, "fotos/pol-roja-m.png")
        with Image.open(Path(self._temporal.name) / relativa) as guardada:
            self.assertLessEqual(max(guardada.size), self.controlador.LADO_FOTO)


class SeparacionTests(unittest.TestCase):
    def test_modelo_persistencia_y_controlador_no_importan_tkinter(self):
        raiz = Path(__file__).resolve().parents[1] / "src" / "smartclothes"
        for carpeta in ("modelo", "persistencia", "controladores"):
            for archivo in (raiz / carpeta).glob("*.py"):
                texto = archivo.read_text(encoding="utf-8")
                self.assertNotIn("tkinter", texto, archivo.name)

    def test_las_vistas_no_descuentan_stock(self):
        raiz = Path(__file__).resolve().parents[1] / "src" / "smartclothes" / "vista"
        for archivo in raiz.glob("*.py"):
            texto = archivo.read_text(encoding="utf-8")
            for prohibido in (".descontar(", ".reponer(", "._stock", "._estado"):
                self.assertNotIn(prohibido, texto, archivo.name)


class InterfazTests(unittest.TestCase):
    def setUp(self):
        try:
            import tkinter as tk

            sonda = tk.Tk()
            sonda.withdraw()
            sonda.destroy()
        except Exception as error:
            self.skipTest(f"Tk no disponible: {error}")
        self._temporal = tempfile.TemporaryDirectory()
        from smartclothes.controladores.controlador import Controlador
        from smartclothes.vista.aplicacion import Aplicacion
        import smartclothes.vista.comun as comun
        import smartclothes.vista.comprobantes as comprobantes
        import smartclothes.vista.mermas as mermas
        import smartclothes.vista.productos as productos
        import smartclothes.vista.tiendas as tiendas
        import smartclothes.vista.traslados as traslados

        self.errores = comun.mostrar_error = MagicMock()
        for modulo in (productos, tiendas, traslados, mermas, comprobantes):
            modulo.informar = MagicMock()
            if hasattr(modulo, "mostrar_error"):
                modulo.mostrar_error = MagicMock()
            if hasattr(modulo, "pedir_confirmacion"):
                modulo.pedir_confirmacion = MagicMock(return_value=True)
        self.app = Aplicacion(Controlador(self._temporal.name))
        self.app.withdraw()
        self.app.update_idletasks()

    def tearDown(self):
        self.app.destroy()
        self._temporal.cleanup()

    def test_buscador_sugiere_por_sku_o_nombre(self):
        from smartclothes.vista.comun import ComboBuscador

        combo = ComboBuscador(self.app)
        opciones = [("CAL-DEP-BL-41", "CAL-DEP-BL-41 Zapatilla Runner"), ("CAL-FOR-NE-42", "CAL-FOR-NE-42 Zapato Oxford"),
                    ("POL-BAS-NE-L", "POL-BAS-NE-L Polera Básica")]
        combo.opciones(opciones)
        tecla = type("Tecla", (), {"keysym": "a"})()
        combo.set("zapato")
        combo._al_escribir(tecla)
        self.assertEqual([valor for valor, _ in combo._coincidencias], ["CAL-FOR-NE-42"])
        combo.set("cal")
        combo._al_escribir(tecla)
        self.assertEqual(len(combo._coincidencias), 2)
        combo._lista.selection_set(1)
        combo._elegir_resaltada()
        self.assertEqual(combo.get(), "CAL-FOR-NE-42")
        combo._lista_completa()
        self.assertEqual(len(combo["values"]), 3, "La flecha siempre muestra todas las prendas")

    def test_flujo_desde_las_pantallas(self):
        self.app._botones_nav["productos"].invoke()
        self.assertIs(self.app._actual, self.app._pantallas["productos"])
        productos = self.app._pantallas["productos"]
        productos.tipo.set("Pantalón")
        productos._actualizar_tipo()
        productos.sku.set("pan-slim-az-40")
        productos.nombre.set("Jeans Slim")
        productos.talla.set("40")
        productos.color.set("Azul")
        productos.extra.set("Slim")
        productos.linea.set("Dama")
        productos.foto.set("fotos/jeans.png")
        productos.stock.set("5")
        productos.registrar()
        self.assertEqual(productos.tabla.get_children(), ("PAN-SLIM-AZ-40",))

        tiendas = self.app._pantallas["tiendas"]
        self.app.mostrar("tiendas")
        tiendas.codigo.set("T-CENTRO")
        tiendas.nombre.set("Centro")
        tiendas.direccion.set("Ahumada 120")
        tiendas.registrar()

        traslados = self.app._pantallas["traslados"]
        self.app.mostrar("traslados")
        traslados.crear()
        folio = traslados.tabla.get_children()[0]
        traslados.sku.set("PAN-SLIM-AZ-40")
        traslados.cantidad.set("9")
        traslados.agregar()
        self.errores.assert_called()
        traslados.cantidad.set("5")
        traslados.agregar()
        self.assertEqual(traslados.transporte.get(), "Camión 3/4 (liviano)")
        traslados.confirmar()
        controlador = self.app.controlador
        self.assertEqual(controlador.obtener_orden(folio).estado, EstadoOrden.CONFIRMADA)
        producto = controlador.obtener_producto("PAN-SLIM-AZ-40")
        self.assertEqual((producto.stock, producto.estado), (0, EstadoProducto.AGOTADO))
        self.assertIs(self.app._actual, self.app._pantallas["comprobantes"])
        texto = self.app._pantallas["comprobantes"].hoja.texto_visible()
        self.assertIn(folio, texto)
        self.assertIn("Camión 3/4", texto)
        self.assertIn("Recibido por (tienda)", texto)

        self.app.mostrar("productos")
        productos.tabla.selection_set("PAN-SLIM-AZ-40")
        productos.al_seleccionar()
        productos.cantidad_ingreso.set("2")
        productos.ingresar()
        self.assertEqual(controlador.obtener_producto("PAN-SLIM-AZ-40").stock, 2)

        mermas = self.app._pantallas["mermas"]
        self.app.mostrar("mermas")
        mermas.sku.set("PAN-SLIM-AZ-40")
        mermas.cantidad.set("1")
        mermas.motivo.set("Daño")
        mermas.observacion.insert("1.0", "Cierre roto al revisar")
        mermas.registrar()
        self.assertEqual(controlador.obtener_producto("PAN-SLIM-AZ-40").stock, 1)
        self.assertEqual(len(controlador.listar_mermas()), 1)

        self.app.mostrar("inicio")
        guardado = json.loads((Path(self._temporal.name) / "traslados.json").read_text(encoding="utf-8"))
        self.assertEqual(guardado[0]["estado"], "CONFIRMADA")


if __name__ == "__main__":
    unittest.main()
