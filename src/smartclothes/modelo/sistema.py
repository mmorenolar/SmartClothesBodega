"""SmartClothes coordina la bodega principal: catálogo, tiendas, traslados y mermas.

Las ventanas no viven aquí: esta clase solo aplica reglas y usa el repositorio.
El stock solo cambia a través de los métodos encapsulados de Producto.
"""

from datetime import date

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.modelo.producto import (
    EstadoProducto,
    Producto,
    crear_producto,
    producto_desde_diccionario,
)
from smartclothes.modelo.salida import (
    EstadoOrden,
    MotivoMerma,
    OrdenTraslado,
    RegistroMerma,
    SalidaBodega,
)
from smartclothes.modelo.tienda import Tienda
from smartclothes.modelo.transporte import TRANSPORTES, PlanDespacho, Transporte
from smartclothes.modelo.validacion import exigir_entero, exigir_fecha, opcion, sku_valido, texto_obligatorio
from smartclothes.persistencia.repositorio_json import RepositorioJSON

PREFIJO_TRASLADO = "OT"
PREFIJO_MERMA = "ME"


class SmartClothes:
    def __init__(self, repositorio: RepositorioJSON):
        self._repositorio = repositorio
        self._productos: dict[str, Producto] = {}
        self._tiendas: dict[str, Tienda] = {}
        self._ordenes: dict[str, OrdenTraslado] = {}
        self._mermas: dict[str, RegistroMerma] = {}
        self._folios = {PREFIJO_TRASLADO: 0, PREFIJO_MERMA: 0}
        self.cargar()

    @property
    def advertencias(self) -> tuple[str, ...]:
        return tuple(self._repositorio.advertencias)

    # ----- Carga y guardado -----

    def cargar(self) -> None:
        self._productos.clear()
        self._tiendas.clear()
        self._ordenes.clear()
        self._mermas.clear()
        for datos in self._repositorio.cargar_lista("productos"):
            self._incorporar(producto_desde_diccionario, datos, self._productos, "Producto")
        for datos in self._repositorio.cargar_lista("tiendas"):
            self._incorporar(Tienda.desde_diccionario, datos, self._tiendas, "Tienda")
        for datos in self._repositorio.cargar_lista("traslados"):
            self._incorporar(OrdenTraslado.desde_diccionario, datos, self._ordenes, "Orden de traslado")
        for datos in self._repositorio.cargar_lista("mermas"):
            self._incorporar(RegistroMerma.desde_diccionario, datos, self._mermas, "Merma")
        guardados = self._repositorio.cargar_objeto("folios")
        for prefijo, documentos in ((PREFIJO_TRASLADO, self._ordenes), (PREFIJO_MERMA, self._mermas)):
            valor = guardados.get(prefijo, 0)
            contador = valor if type(valor) is int and valor >= 0 else 0
            self._folios[prefijo] = max(contador, self._mayor_folio(prefijo, documentos))

    def guardar(self) -> None:
        self._repositorio.guardar("productos", [item.a_diccionario() for item in self._productos.values()])
        self._repositorio.guardar("tiendas", [item.a_diccionario() for item in self._tiendas.values()])
        self._repositorio.guardar("traslados", [item.a_diccionario() for item in self._ordenes.values()])
        self._repositorio.guardar("mermas", [item.a_diccionario() for item in self._mermas.values()])
        self._repositorio.guardar("folios", dict(self._folios))

    # ----- Consultas -----

    def listar_productos(self) -> tuple[Producto, ...]:
        return tuple(self._productos.values())

    def listar_tiendas(self) -> tuple[Tienda, ...]:
        return tuple(self._tiendas.values())

    def listar_ordenes(self) -> tuple[OrdenTraslado, ...]:
        return tuple(self._ordenes.values())

    def listar_mermas(self) -> tuple[RegistroMerma, ...]:
        return tuple(self._mermas.values())

    def listar_documentos(self) -> tuple[SalidaBodega, ...]:
        """Traslados confirmados y mermas: todo lo que tiene comprobante."""
        confirmadas = [orden for orden in self._ordenes.values() if orden.aplicada]
        return tuple(confirmadas + list(self._mermas.values()))

    def obtener_producto(self, sku: str) -> Producto:
        return self._buscar(self._productos, str(sku).strip().upper(), f"No existe un producto con SKU {sku}")

    def obtener_tienda(self, codigo: str) -> Tienda:
        return self._buscar(self._tiendas, str(codigo).strip().upper(), "Tienda inexistente")

    def obtener_orden(self, folio: str) -> OrdenTraslado:
        return self._buscar(self._ordenes, folio, "Orden de traslado inexistente")

    def obtener_merma(self, folio: str) -> RegistroMerma:
        return self._buscar(self._mermas, folio, "Registro de merma inexistente")

    def obtener_documento(self, folio: str) -> SalidaBodega:
        if folio in self._ordenes:
            return self._ordenes[folio]
        return self.obtener_merma(folio)

    def stock_disponible(self, sku: str) -> int:
        """Stock físico menos lo reservado en órdenes en borrador."""
        producto = self.obtener_producto(sku)
        if not producto.disponible:
            return 0
        disponible = producto.stock - self._stock_comprometido(producto.sku)
        return disponible if disponible > 0 else 0

    def acciones(self, folio: str) -> dict[str, bool]:
        orden = self.obtener_orden(folio)
        borrador = orden.estado is EstadoOrden.BORRADOR
        return {
            "puede_editar_items": borrador,
            "puede_confirmar": borrador and bool(orden.detalles),
            "puede_anular": borrador,
            "tiene_comprobante": orden.aplicada,
        }

    def resumen(self) -> dict:
        productos = self._productos.values()
        return {
            "productos": len(self._productos),
            "disponibles": sum(1 for item in productos if item.estado is EstadoProducto.DISPONIBLE),
            "agotados": sum(1 for item in productos if item.estado is EstadoProducto.AGOTADO),
            "unidades": sum(item.stock for item in productos),
            "tiendas": len(self._tiendas),
            "ordenes": {
                estado.etiqueta: sum(1 for orden in self._ordenes.values() if orden.estado is estado)
                for estado in EstadoOrden
            },
            "mermas": len(self._mermas),
            "unidades_mermadas": sum(merma.cantidad for merma in self._mermas.values()),
        }

    def emitir_comprobante(self, folio: str) -> str:
        """Polimorfismo: cada documento arma su propio comprobante."""
        documento = self.obtener_documento(folio)
        catalogo = {tienda.codigo: tienda.identificacion for tienda in self._tiendas.values()}
        return documento.comprobante(catalogo)

    # ----- Productos -----

    def registrar_producto(self, tipo: str, sku: str, nombre: str, foto: str, stock: int, talla: str,
                           color: str, linea: str, extra: object = None) -> Producto:
        producto = crear_producto(tipo, sku, nombre, foto, stock, talla, color, linea, extra)
        if producto.sku in self._productos:
            raise ReglaNegocioError(f"Ya existe un producto con SKU {producto.sku}")
        self._productos[producto.sku] = producto
        self.guardar()
        return producto

    def editar_producto(self, sku: str, nombre: str, foto: str, talla: str, color: str, linea: str,
                        extra: object = None) -> Producto:
        producto = self.obtener_producto(sku)
        etiqueta, opciones = producto.opciones_extra()  # cada prenda sabe cuál es su atributo especial
        if etiqueta:
            extra = opcion(extra, opciones, etiqueta)
        producto.actualizar(nombre, foto, talla, color, linea)
        producto.actualizar_especifico(extra)
        self.guardar()
        return producto

    def ingresar_stock(self, sku: str, cantidad: int) -> Producto:
        """Recepción de mercadería en bodega. Si estaba Agotado, vuelve a Disponible."""
        producto = self.obtener_producto(sku)
        producto.reponer(cantidad)
        self.guardar()
        return producto

    def eliminar_producto(self, sku: str) -> None:
        producto = self.obtener_producto(sku)
        en_uso = any(orden.contiene(producto.sku) for orden in self._ordenes.values()) or any(
            merma.contiene(producto.sku) for merma in self._mermas.values()
        )
        if en_uso:
            raise ReglaNegocioError("No se puede eliminar un producto con traslados o mermas registradas")
        del self._productos[producto.sku]
        self.guardar()

    # ----- Tiendas -----

    def registrar_tienda(self, codigo: str, nombre: str, direccion: str) -> Tienda:
        tienda = Tienda(codigo, nombre, direccion)
        if tienda.codigo in self._tiendas:
            raise ReglaNegocioError(f"Ya existe una tienda con código {tienda.codigo}")
        self._tiendas[tienda.codigo] = tienda
        self.guardar()
        return tienda

    def editar_tienda(self, codigo: str, nombre: str, direccion: str) -> Tienda:
        tienda = self.obtener_tienda(codigo)
        tienda.actualizar(nombre, direccion)
        self.guardar()
        return tienda

    def eliminar_tienda(self, codigo: str) -> None:
        tienda = self.obtener_tienda(codigo)
        if any(orden.tienda_codigo == tienda.codigo for orden in self._ordenes.values()):
            raise ReglaNegocioError("No se puede eliminar una tienda que tiene órdenes de traslado")
        del self._tiendas[tienda.codigo]
        self.guardar()

    # ----- Órdenes de traslado -----

    def crear_orden(self, tienda_codigo: str, fecha_despacho: date, hoy: date | None = None) -> OrdenTraslado:
        tienda = self.obtener_tienda(tienda_codigo)
        fecha = exigir_fecha(fecha_despacho, "Fecha de despacho")
        if fecha < (hoy or date.today()):
            raise ReglaNegocioError("La fecha de despacho no puede ser anterior a hoy")
        orden = OrdenTraslado(self._siguiente_folio(PREFIJO_TRASLADO), fecha, tienda.codigo)
        self._ordenes[orden.folio] = orden
        self.guardar()
        return orden

    def agregar_a_orden(self, folio: str, sku: str, cantidad: int) -> OrdenTraslado:
        orden = self.obtener_orden(folio)
        if orden.estado is not EstadoOrden.BORRADOR:
            raise ReglaNegocioError("Solo se modifican los productos de una orden en borrador")
        producto = self.obtener_producto(sku_valido(sku))
        cantidad = exigir_entero(cantidad, "Cantidad", minimo=1)
        producto.validar_salida(cantidad)
        disponible = self.stock_disponible(producto.sku)
        if cantidad > disponible:
            raise ReglaNegocioError(
                f"No hay stock suficiente de {producto.sku}. Disponible para traslado: {disponible}"
            )
        orden.agregar(producto, cantidad)
        self.guardar()
        return orden

    def quitar_de_orden(self, folio: str, sku: str) -> OrdenTraslado:
        orden = self.obtener_orden(folio)
        orden.quitar(str(sku).strip().upper())
        self.guardar()
        return orden

    def cotizar_despachos(self, folio: str) -> list[tuple[Transporte, PlanDespacho | None, str]]:
        """Pregunta a cada camión si sirve y cuánto cuesta. No hay un if por tipo de camión."""
        orden = self.obtener_orden(folio)
        unidades = orden.unidades
        cotizaciones = []
        for clase in TRANSPORTES:
            transporte = clase()
            motivo = transporte.motivo_rechazo(unidades) if unidades else "la orden no tiene prendas"
            plan = None if motivo else transporte.planificar(unidades)
            cotizaciones.append((transporte, plan, motivo or ""))
        return cotizaciones

    def transporte_sugerido(self, folio: str) -> Transporte | None:
        """El camión más chico que alcanza para la carga: así se aprovecha mejor su espacio."""
        aptas = [(plan.capacidad, transporte) for transporte, plan, _motivo in self.cotizar_despachos(folio) if plan]
        return min(aptas, key=lambda item: item[0])[1] if aptas else None

    def confirmar_orden(self, folio: str, transporte: Transporte) -> str:
        """Valida, planifica el despacho, descuenta el stock y devuelve el comprobante."""
        orden = self.obtener_orden(folio)
        plan = orden.cotizar(transporte)
        orden.asignar_despacho(plan)
        self._aplicar_salida(orden)
        self.guardar()
        return self.emitir_comprobante(orden.folio)

    def anular_orden(self, folio: str) -> OrdenTraslado:
        orden = self.obtener_orden(folio)
        orden.anular()
        self.guardar()
        return orden

    # ----- Mermas -----

    def registrar_merma(self, sku: str, cantidad: int, motivo: MotivoMerma, observacion: str,
                        fecha: date | None = None) -> RegistroMerma:
        producto = self.obtener_producto(sku_valido(sku))
        merma = RegistroMerma(
            self._proximo_folio(PREFIJO_MERMA),
            fecha or date.today(),
            producto,
            cantidad,
            motivo,
            observacion,
        )
        self._aplicar_salida(merma)
        self._siguiente_folio(PREFIJO_MERMA)
        self._mermas[merma.folio] = merma
        self.guardar()
        return merma

    # ----- Métodos internos -----

    def _aplicar_salida(self, salida: SalidaBodega) -> None:
        """Polimorfismo: recorre lineas() sin saber si es traslado o merma.

        Primero valida todo. Si algo falla a mitad de camino, repone lo descontado.
        """
        pendientes: list[tuple[Producto, int]] = []
        for sku, cantidad in salida.lineas():
            producto = self.obtener_producto(sku)
            producto.validar_salida(cantidad)
            pendientes.append((producto, cantidad))
        aplicados: list[tuple[Producto, int]] = []
        try:
            for producto, cantidad in pendientes:
                producto.descontar(cantidad)
                aplicados.append((producto, cantidad))
            salida.marcar_aplicada()
        except Exception:
            for producto, cantidad in reversed(aplicados):
                producto.reponer(cantidad)
            raise

    def _stock_comprometido(self, sku: str) -> int:
        return sum(
            orden.cantidad_de(sku) for orden in self._ordenes.values() if orden.estado is EstadoOrden.BORRADOR
        )

    def _proximo_folio(self, prefijo: str) -> str:
        return f"{prefijo}-{self._folios[prefijo] + 1:06d}"

    def _siguiente_folio(self, prefijo: str) -> str:
        folio = self._proximo_folio(prefijo)
        self._folios[prefijo] += 1
        return folio

    @staticmethod
    def _mayor_folio(prefijo: str, documentos: dict) -> int:
        mayor = 0
        for folio in documentos:
            numero = folio.removeprefix(f"{prefijo}-")
            if numero.isdigit():
                mayor = max(mayor, int(numero))
        return mayor

    def _incorporar(self, fabrica, datos: dict, destino: dict, etiqueta: str) -> None:
        try:
            entidad = fabrica(datos)
        except (ReglaNegocioError, KeyError, TypeError) as error:
            self._repositorio.advertencias.append(f"{etiqueta} omitido: {error}")
            return
        if entidad.id in destino:
            self._repositorio.advertencias.append(f"{etiqueta} duplicado omitido: {entidad.id}")
            return
        destino[entidad.id] = entidad

    @staticmethod
    def _buscar(coleccion: dict, clave: str, mensaje: str):
        try:
            return coleccion[texto_obligatorio(clave, "Identificador")]
        except KeyError as error:
            raise ReglaNegocioError(mensaje) from error
