"""Salidas de bodega: Orden de Traslado y Registro de Merma.

Ambas especializan SalidaBodega. La bodega descuenta stock recorriendo
lineas() y emite el documento con comprobante(), sin preguntar qué clase
concreta recibió (polimorfismo).

Estados de la orden:
BORRADOR → CONFIRMADA
    └────→ ANULADA
"""

from abc import ABC, abstractmethod
from datetime import date
from enum import Enum

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.modelo.producto import Producto
from smartclothes.modelo.transporte import PlanDespacho, Transporte
from smartclothes.modelo.validacion import (
    exigir_entero,
    exigir_fecha,
    fecha_a_texto,
    fecha_desde_texto,
    texto_obligatorio,
)


class SalidaBodega(ABC):
    """Contrato común de todo documento que saca unidades de la bodega."""

    def __init__(self, folio: str, fecha: date):
        self._folio = texto_obligatorio(folio, "Folio")
        self._fecha = exigir_fecha(fecha, "Fecha")

    @property
    def folio(self) -> str:
        return self._folio

    @property
    def id(self) -> str:
        return self._folio

    @property
    def fecha(self) -> date:
        return self._fecha

    @property
    def fecha_texto(self) -> str:
        return fecha_a_texto(self._fecha)

    @property
    def unidades(self) -> int:
        return sum(cantidad for _sku, cantidad in self.lineas())

    @property
    @abstractmethod
    def tipo(self) -> str:
        """Clave estable para guardar el documento."""

    @property
    @abstractmethod
    def nombre_documento(self) -> str:
        """Título del comprobante."""

    @property
    @abstractmethod
    def aplicada(self) -> bool:
        """True cuando las unidades ya salieron de bodega."""

    @abstractmethod
    def lineas(self) -> tuple[tuple[str, int], ...]:
        """Pares (SKU, cantidad) que salen de bodega."""

    @abstractmethod
    def _cuerpo_comprobante(self, catalogo: dict) -> list[str]:
        """Líneas propias del documento concreto."""

    @abstractmethod
    def marcar_aplicada(self) -> None:
        """La bodega avisa que ya descontó el stock."""

    @abstractmethod
    def a_diccionario(self) -> dict:
        """Datos para JSON."""

    def comprobante(self, catalogo: dict | None = None) -> str:
        """Plantilla común. Cada subclase aporta su cuerpo."""
        if not self.aplicada:
            raise ReglaNegocioError("El comprobante se emite cuando el documento está confirmado")
        separador = "=" * 64
        lineas = [
            separador,
            "SMART CLOTHES — BODEGA PRINCIPAL",
            self.nombre_documento.upper(),
            separador,
            f"Folio: {self._folio}",
        ]
        lineas.extend(self._cuerpo_comprobante(catalogo or {}))
        lineas.append(separador)
        return "\n".join(lineas)


class DetalleTraslado:
    """Una línea de la orden. Copia los datos de la prenda al momento de agregarla."""

    def __init__(self, sku: str, nombre: str, foto: str, talla: str, color: str, cantidad: int):
        self._sku = texto_obligatorio(sku, "SKU")
        self._nombre = texto_obligatorio(nombre, "Nombre")
        self._foto = texto_obligatorio(foto, "Foto")
        self._talla = texto_obligatorio(talla, "Talla")
        self._color = texto_obligatorio(color, "Color")
        self._cantidad = exigir_entero(cantidad, "Cantidad", minimo=1)

    @classmethod
    def desde_producto(cls, producto: Producto, cantidad: int) -> "DetalleTraslado":
        return cls(producto.sku, producto.nombre, producto.foto, producto.talla, producto.color, cantidad)

    @property
    def sku(self) -> str:
        return self._sku

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def foto(self) -> str:
        return self._foto

    @property
    def talla(self) -> str:
        return self._talla

    @property
    def color(self) -> str:
        return self._color

    @property
    def cantidad(self) -> int:
        return self._cantidad

    def aumentar(self, cantidad: int) -> None:
        self._cantidad += exigir_entero(cantidad, "Cantidad", minimo=1)

    def a_diccionario(self) -> dict:
        return {
            "sku": self._sku,
            "nombre": self._nombre,
            "foto": self._foto,
            "talla": self._talla,
            "color": self._color,
            "cantidad": self._cantidad,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "DetalleTraslado":
        try:
            return cls(
                datos["sku"], datos["nombre"], datos["foto"], str(datos["talla"]), datos["color"], datos["cantidad"]
            )
        except (KeyError, TypeError) as error:
            raise ReglaNegocioError("Línea de traslado incompleta") from error


class EstadoOrden(Enum):
    BORRADOR = "BORRADOR"
    CONFIRMADA = "CONFIRMADA"
    ANULADA = "ANULADA"

    @property
    def etiqueta(self) -> str:
        return {
            EstadoOrden.BORRADOR: "Borrador",
            EstadoOrden.CONFIRMADA: "Confirmada",
            EstadoOrden.ANULADA: "Anulada",
        }[self]


_TRANSICIONES = {
    EstadoOrden.BORRADOR: {EstadoOrden.CONFIRMADA, EstadoOrden.ANULADA},
    EstadoOrden.CONFIRMADA: set(),
    EstadoOrden.ANULADA: set(),
}


class OrdenTraslado(SalidaBodega):
    """Envío de prendas desde la bodega principal a una tienda."""

    def __init__(self, folio: str, fecha_despacho: date, tienda_codigo: str):
        super().__init__(folio, fecha_despacho)
        self._tienda_codigo = texto_obligatorio(tienda_codigo, "Tienda destino")
        self._detalles: list[DetalleTraslado] = []
        self._estado = EstadoOrden.BORRADOR
        self._despacho: PlanDespacho | None = None

    @property
    def tipo(self) -> str:
        return "traslado"

    @property
    def nombre_documento(self) -> str:
        return "Comprobante de Orden de Traslado"

    @property
    def fecha_despacho(self) -> date:
        return self._fecha

    @property
    def tienda_codigo(self) -> str:
        return self._tienda_codigo

    @property
    def estado(self) -> EstadoOrden:
        return self._estado

    @property
    def detalles(self) -> tuple[DetalleTraslado, ...]:
        return tuple(self._detalles)

    @property
    def despacho(self) -> PlanDespacho | None:
        return self._despacho

    @property
    def aplicada(self) -> bool:
        return self._estado is EstadoOrden.CONFIRMADA

    def lineas(self) -> tuple[tuple[str, int], ...]:
        return tuple((detalle.sku, detalle.cantidad) for detalle in self._detalles)

    def cantidad_de(self, sku: str) -> int:
        for detalle in self._detalles:
            if detalle.sku == sku:
                return detalle.cantidad
        return 0

    def contiene(self, sku: str) -> bool:
        return any(detalle.sku == sku for detalle in self._detalles)

    def agregar(self, producto: Producto, cantidad: int) -> None:
        self._exigir_borrador()
        cantidad = exigir_entero(cantidad, "Cantidad", minimo=1)
        for detalle in self._detalles:
            if detalle.sku == producto.sku:
                detalle.aumentar(cantidad)
                return
        self._detalles.append(DetalleTraslado.desde_producto(producto, cantidad))

    def quitar(self, sku: str) -> None:
        self._exigir_borrador()
        restantes = [detalle for detalle in self._detalles if detalle.sku != sku]
        if len(restantes) == len(self._detalles):
            raise ReglaNegocioError("Ese SKU no está en la orden")
        self._detalles = restantes

    def validar_puede_confirmarse(self) -> None:
        if self._estado is not EstadoOrden.BORRADOR:
            raise ReglaNegocioError(f"La orden {self._folio} ya está {self._estado.etiqueta.lower()}")
        if not self._detalles:
            raise ReglaNegocioError("Agrega al menos un producto antes de confirmar")

    def cotizar(self, transporte: Transporte) -> PlanDespacho:
        """Polimorfismo: el camión concreto decide si sirve y cuánto cuesta."""
        self.validar_puede_confirmarse()
        if not isinstance(transporte, Transporte):
            raise ReglaNegocioError("Transporte no válido")
        return transporte.planificar(self.unidades)

    def asignar_despacho(self, plan: PlanDespacho) -> None:
        self.validar_puede_confirmarse()
        if plan.unidades != self.unidades:
            raise ReglaNegocioError("El despacho no corresponde a las unidades de la orden")
        self._despacho = plan

    def marcar_aplicada(self) -> None:
        self.validar_puede_confirmarse()
        if self._despacho is None:
            raise ReglaNegocioError("Elige el transporte antes de confirmar")
        self._transicionar(EstadoOrden.CONFIRMADA)

    def anular(self) -> None:
        if self._estado is EstadoOrden.CONFIRMADA:
            raise ReglaNegocioError("Una orden confirmada ya salió de bodega y no se anula")
        self._transicionar(EstadoOrden.ANULADA)

    def _cuerpo_comprobante(self, catalogo: dict) -> list[str]:
        tienda = catalogo.get(self._tienda_codigo, self._tienda_codigo)
        lineas = [
            f"Fecha de despacho: {self.fecha_texto}",
            f"Tienda destino: {tienda}",
            "-" * 64,
            f"{'SKU':<16}{'Nombre':<20}{'Talla':<7}{'Color':<10}{'Cant.':>6}",
        ]
        for detalle in self._detalles:
            lineas.append(
                f"{detalle.sku:<16}{detalle.nombre[:19]:<20}{detalle.talla:<7}{detalle.color[:9]:<10}{detalle.cantidad:>6}"
            )
            lineas.append(f"{'':<16}Foto: {detalle.foto}")
        lineas.append("-" * 64)
        lineas.append(f"Total de unidades enviadas: {self.unidades}")
        if self._despacho is not None:
            lineas.append(f"Transporte: {self._despacho.resumen()}")
        return lineas

    def _exigir_borrador(self) -> None:
        if self._estado is not EstadoOrden.BORRADOR:
            raise ReglaNegocioError("Solo se modifican los productos de una orden en borrador")

    def _transicionar(self, nuevo: EstadoOrden) -> None:
        if nuevo not in _TRANSICIONES[self._estado]:
            raise ReglaNegocioError(f"No se puede pasar de {self._estado.etiqueta} a {nuevo.etiqueta}")
        self._estado = nuevo

    def a_diccionario(self) -> dict:
        return {
            "folio": self._folio,
            "tipo": self.tipo,
            "fecha_despacho": self.fecha_texto,
            "tienda_codigo": self._tienda_codigo,
            "estado": self._estado.value,
            "despacho": None if self._despacho is None else self._despacho.a_diccionario(),
            "detalles": [detalle.a_diccionario() for detalle in self._detalles],
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "OrdenTraslado":
        try:
            orden = cls(
                datos["folio"],
                fecha_desde_texto(datos["fecha_despacho"], "Fecha de despacho"),
                datos["tienda_codigo"],
            )
            orden._detalles = [DetalleTraslado.desde_diccionario(item) for item in datos["detalles"]]
            orden._estado = EstadoOrden(datos["estado"])
            despacho = datos.get("despacho")
            orden._despacho = None if despacho is None else PlanDespacho.desde_diccionario(despacho)
        except (KeyError, TypeError, ValueError) as error:
            raise ReglaNegocioError("Orden de traslado guardada incompleta o inválida") from error
        if orden._estado is EstadoOrden.CONFIRMADA and not orden._detalles:
            raise ReglaNegocioError("Una orden confirmada debe tener productos")
        if orden._estado is EstadoOrden.CONFIRMADA and orden._despacho is None:
            raise ReglaNegocioError("Una orden confirmada debe tener transporte")
        return orden


class MotivoMerma(Enum):
    DANO = "DANO"
    PERDIDA = "PERDIDA"
    FALLA_FABRICA = "FALLA_FABRICA"

    @property
    def etiqueta(self) -> str:
        return {
            MotivoMerma.DANO: "Daño",
            MotivoMerma.PERDIDA: "Pérdida",
            MotivoMerma.FALLA_FABRICA: "Falla de fábrica",
        }[self]

    @classmethod
    def desde_etiqueta(cls, texto: str) -> "MotivoMerma":
        for motivo in cls:
            if motivo.etiqueta.lower() == str(texto).strip().lower():
                return motivo
        raise ReglaNegocioError("El motivo debe ser Daño, Pérdida o Falla de fábrica")


class RegistroMerma(SalidaBodega):
    """Baja de un producto por daño, pérdida o falla de fábrica."""

    LARGO_MINIMO_OBSERVACION = 10

    def __init__(self, folio: str, fecha: date, producto: Producto | DetalleTraslado, cantidad: int,
                 motivo: MotivoMerma, observacion: str):
        super().__init__(folio, fecha)
        if not isinstance(motivo, MotivoMerma):
            raise ReglaNegocioError("Selecciona un motivo de merma")
        observacion_limpia = texto_obligatorio(observacion, "Observación")
        if len(observacion_limpia) < self.LARGO_MINIMO_OBSERVACION:
            raise ReglaNegocioError(
                f"La observación debe justificar la baja (mínimo {self.LARGO_MINIMO_OBSERVACION} caracteres)"
            )
        self._sku = producto.sku
        self._nombre = producto.nombre
        self._talla = producto.talla
        self._color = producto.color
        self._cantidad = exigir_entero(cantidad, "Cantidad", minimo=1)
        self._motivo = motivo
        self._observacion = observacion_limpia
        self._aplicada = False

    @property
    def tipo(self) -> str:
        return "merma"

    @property
    def nombre_documento(self) -> str:
        return "Registro de Merma"

    @property
    def sku(self) -> str:
        return self._sku

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def talla(self) -> str:
        return self._talla

    @property
    def color(self) -> str:
        return self._color

    @property
    def cantidad(self) -> int:
        return self._cantidad

    @property
    def motivo(self) -> MotivoMerma:
        return self._motivo

    @property
    def observacion(self) -> str:
        return self._observacion

    @property
    def aplicada(self) -> bool:
        return self._aplicada

    def lineas(self) -> tuple[tuple[str, int], ...]:
        return ((self._sku, self._cantidad),)

    def contiene(self, sku: str) -> bool:
        return self._sku == sku

    def marcar_aplicada(self) -> None:
        if self._aplicada:
            raise ReglaNegocioError("Esta merma ya fue descontada")
        self._aplicada = True

    def _cuerpo_comprobante(self, catalogo: dict) -> list[str]:
        return [
            f"Fecha de registro: {self.fecha_texto}",
            "-" * 64,
            f"Producto: {self._sku} — {self._nombre}",
            f"Talla: {self._talla}    Color: {self._color}",
            f"Cantidad dada de baja: {self._cantidad}",
            f"Motivo: {self._motivo.etiqueta}",
            f"Observación: {self._observacion}",
        ]

    def a_diccionario(self) -> dict:
        return {
            "folio": self._folio,
            "tipo": self.tipo,
            "fecha": self.fecha_texto,
            "sku": self._sku,
            "nombre": self._nombre,
            "talla": self._talla,
            "color": self._color,
            "cantidad": self._cantidad,
            "motivo": self._motivo.value,
            "observacion": self._observacion,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "RegistroMerma":
        try:
            prenda = DetalleTraslado(
                datos["sku"], datos["nombre"], "-", str(datos["talla"]), datos["color"], datos["cantidad"]
            )
            merma = cls(
                datos["folio"],
                fecha_desde_texto(datos["fecha"], "Fecha"),
                prenda,
                datos["cantidad"],
                MotivoMerma(datos["motivo"]),
                datos["observacion"],
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ReglaNegocioError("Registro de merma guardado incompleto o inválido") from error
        merma._aplicada = True
        return merma
