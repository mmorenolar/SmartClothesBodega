"""Traduce la interfaz al modelo. No dibuja ventanas ni decide el stock."""

from pathlib import Path

from smartclothes.modelo.formato import pesos
from smartclothes.modelo.errores import PersistenciaError, ReglaNegocioError
from smartclothes.modelo.producto import TIPOS_PRODUCTO, Calzado, Pantalon, Producto
from smartclothes.modelo.salida import MotivoMerma
from smartclothes.modelo.sistema import SmartClothes
from smartclothes.modelo.transporte import TRANSPORTES, transporte_por_nombre
from smartclothes.modelo.validacion import fecha_desde_texto
from smartclothes.persistencia.repositorio_json import RepositorioJSON
from smartclothes.rutas import directorio_datos


class Controlador:
    def __init__(self, directorio: str | Path | None = None):
        self._directorio = Path(directorio) if directorio is not None else directorio_datos()
        self._sistema = SmartClothes(RepositorioJSON(self._directorio))

    @property
    def directorio(self) -> Path:
        return self._directorio

    @property
    def advertencia(self) -> str:
        return "\n".join(self._sistema.advertencias)

    # ----- Datos para las pantallas -----

    @staticmethod
    def tipos_producto() -> tuple[str, ...]:
        return tuple(TIPOS_PRODUCTO)

    @staticmethod
    def tallas_de(tipo: str) -> tuple[str, ...]:
        clase = TIPOS_PRODUCTO.get(tipo.strip())
        return clase.tallas_validas() if clase else ()

    @staticmethod
    def opciones_extra(tipo: str) -> tuple[str, tuple[str, ...]]:
        """Etiqueta y valores del atributo especial. La polera no tiene."""
        clave = tipo.strip()
        if clave == "Pantalón":
            return "Corte", Pantalon.CORTES
        if clave == "Calzado":
            return "Estilo", Calzado.ESTILOS
        return "", ()

    @staticmethod
    def transportes() -> tuple[str, ...]:
        return tuple(clase().nombre for clase in TRANSPORTES)

    def cotizar_despachos(self, folio: str) -> list[tuple[str, str]]:
        """(nombre del camión, texto con costo y ocupación o motivo por el que no sirve)."""
        filas = []
        for transporte, plan, motivo in self._sistema.cotizar_despachos(folio):
            if plan:
                texto = f"{pesos(plan.costo)} · ocupación {plan.ocupacion}%"
            else:
                texto = f"no apto: {motivo}"
            filas.append((transporte.nombre, texto))
        return filas

    def transporte_sugerido(self, folio: str) -> str:
        transporte = self._sistema.transporte_sugerido(folio)
        return transporte.nombre if transporte else ""

    @staticmethod
    def motivos_merma() -> tuple[str, ...]:
        return tuple(motivo.etiqueta for motivo in MotivoMerma)

    def resumen(self) -> dict:
        return self._sistema.resumen()

    def listar_productos(self):
        return self._sistema.listar_productos()

    def listar_tiendas(self):
        return self._sistema.listar_tiendas()

    def listar_ordenes(self):
        return self._sistema.listar_ordenes()

    def listar_mermas(self):
        return self._sistema.listar_mermas()

    def listar_documentos(self):
        return self._sistema.listar_documentos()

    def obtener_producto(self, sku: str) -> Producto:
        return self._sistema.obtener_producto(sku)

    def obtener_tienda(self, codigo: str):
        return self._sistema.obtener_tienda(codigo)

    def obtener_orden(self, folio: str):
        return self._sistema.obtener_orden(folio)

    def obtener_documento(self, folio: str):
        return self._sistema.obtener_documento(folio)

    def nombre_tienda(self, codigo: str) -> str:
        try:
            return self._sistema.obtener_tienda(codigo).identificacion
        except ReglaNegocioError:
            return f"{codigo} (tienda no disponible)"

    def stock_disponible(self, sku: str) -> int:
        return self._sistema.stock_disponible(sku)

    def acciones(self, folio: str) -> dict[str, bool]:
        return self._sistema.acciones(folio)

    def emitir_comprobante(self, folio: str) -> str:
        self._exigir(folio, "un documento")
        return self._sistema.emitir_comprobante(folio)

    def ruta_foto(self, foto: str) -> Path | None:
        """Ubica la foto relativa a la carpeta de datos. None si no existe."""
        if not foto:
            return None
        ruta = Path(foto)
        if not ruta.is_absolute():
            ruta = self._directorio / ruta
        return ruta if ruta.exists() else None

    def foto_relativa(self, ruta: str) -> str:
        """Si la foto está dentro de la carpeta de datos, guarda la ruta relativa."""
        if not ruta:
            return ""
        try:
            return Path(ruta).resolve().relative_to(self._directorio.resolve()).as_posix()
        except ValueError:
            return ruta

    def exportar_comprobante(self, folio: str, destino: str) -> Path:
        texto = self.emitir_comprobante(folio)
        ruta = Path(self._exigir(destino, "dónde guardar el comprobante"))
        try:
            ruta.write_text(texto + "\n", encoding="utf-8")
        except OSError as error:
            raise PersistenciaError(f"No se pudo guardar el comprobante: {error}") from error
        return ruta

    # ----- Productos -----

    def registrar_producto(self, tipo: str, sku: str, nombre: str, foto: str, stock: str, talla: str,
                           color: str, extra: str):
        clave = self._tipo(tipo)
        return self._sistema.registrar_producto(
            clave, sku, nombre, foto, self._entero(stock, "Stock inicial", 0), talla, color, extra
        )

    def editar_producto(self, sku: str, nombre: str, foto: str, talla: str, color: str, extra: str):
        self._exigir(sku, "un producto")
        return self._sistema.editar_producto(sku, nombre, foto, talla, color, extra)

    def ingresar_stock(self, sku: str, cantidad: str):
        self._exigir(sku, "un producto")
        return self._sistema.ingresar_stock(sku, self._entero(cantidad, "Cantidad a ingresar", 1))

    def eliminar_producto(self, sku: str) -> None:
        self._exigir(sku, "un producto")
        self._sistema.eliminar_producto(sku)

    # ----- Tiendas -----

    def registrar_tienda(self, codigo: str, nombre: str, direccion: str):
        return self._sistema.registrar_tienda(codigo, nombre, direccion)

    def editar_tienda(self, codigo: str, nombre: str, direccion: str):
        self._exigir(codigo, "una tienda")
        return self._sistema.editar_tienda(codigo, nombre, direccion)

    def eliminar_tienda(self, codigo: str) -> None:
        self._exigir(codigo, "una tienda")
        self._sistema.eliminar_tienda(codigo)

    # ----- Órdenes de traslado -----

    def crear_orden(self, tienda_codigo: str, fecha_despacho: str):
        self._exigir(tienda_codigo, "la tienda destino")
        return self._sistema.crear_orden(tienda_codigo, fecha_desde_texto(fecha_despacho, "Fecha de despacho"))

    def agregar_a_orden(self, folio: str, sku: str, cantidad: str):
        self._exigir(folio, "una orden de traslado")
        self._exigir(sku, "un SKU")
        return self._sistema.agregar_a_orden(folio, sku, self._entero(cantidad, "Cantidad", 1))

    def quitar_de_orden(self, folio: str, sku: str):
        self._exigir(folio, "una orden de traslado")
        self._exigir(sku, "la línea que quieres quitar")
        return self._sistema.quitar_de_orden(folio, sku)

    def confirmar_orden(self, folio: str, transporte: str) -> str:
        self._exigir(folio, "una orden de traslado")
        self._exigir(transporte, "el transporte")
        return self._sistema.confirmar_orden(folio, transporte_por_nombre(transporte))

    def anular_orden(self, folio: str):
        self._exigir(folio, "una orden de traslado")
        return self._sistema.anular_orden(folio)

    # ----- Mermas -----

    def registrar_merma(self, sku: str, cantidad: str, motivo: str, observacion: str):
        self._exigir(sku, "un SKU")
        self._exigir(motivo, "un motivo")
        return self._sistema.registrar_merma(
            sku,
            self._entero(cantidad, "Cantidad", 1),
            MotivoMerma.desde_etiqueta(motivo),
            observacion,
        )

    # ----- Conversión de texto -----

    @staticmethod
    def _tipo(tipo: str) -> str:
        if not isinstance(tipo, str) or tipo.strip() not in TIPOS_PRODUCTO:
            raise ReglaNegocioError("Selecciona el tipo de prenda: Pantalón, Calzado o Polera")
        return tipo.strip()

    @staticmethod
    def _exigir(valor: str, campo: str) -> str:
        if not isinstance(valor, str) or not valor.strip():
            raise ReglaNegocioError(f"Selecciona {campo}")
        return valor.strip()

    @staticmethod
    def _entero(texto: str, campo: str, minimo: int) -> int:
        if not isinstance(texto, str):
            raise ReglaNegocioError(f"{campo} debe ser un número entero")
        limpio = texto.strip()
        negativo = limpio.startswith("-")
        digitos = limpio[1:] if negativo else limpio
        if not digitos.isdigit():
            raise ReglaNegocioError(f"{campo} debe ser un número entero, sin puntos ni comas")
        valor = int(digitos) * (-1 if negativo else 1)
        if valor < minimo:
            if minimo == 1:
                raise ReglaNegocioError(f"{campo} debe ser un entero mayor que cero")
            raise ReglaNegocioError(f"{campo} debe ser un entero mayor o igual a cero")
        return valor
