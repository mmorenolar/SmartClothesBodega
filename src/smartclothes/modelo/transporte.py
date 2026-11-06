"""Modalidades de despacho con los camiones propios de la bodega.

Cada camión decide a su manera si puede llevar la carga, según su capacidad
y su carga mínima. Los camiones son de la empresa, así que no hay cobro.

La orden de traslado y el sistema solo conocen el contrato Transporte:
llaman a planificar() sin preguntar qué camión concreto recibieron
(polimorfismo). Para agregar otro vehículo basta con una subclase nueva.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.modelo.validacion import exigir_entero, texto_obligatorio


@dataclass(frozen=True)
class PlanDespacho:
    """Resultado de planificar un viaje. Queda congelado en la orden confirmada."""

    transporte: str
    nombre: str
    unidades: int
    capacidad: int

    @property
    def ocupacion(self) -> int:
        """Porcentaje del camión que se usa."""
        return self.unidades * 100 // self.capacidad

    def resumen(self) -> str:
        return f"{self.nombre} · {self.unidades} de {self.capacidad} prendas · Ocupación {self.ocupacion}%"

    def a_diccionario(self) -> dict:
        return {
            "transporte": self.transporte,
            "nombre": self.nombre,
            "unidades": self.unidades,
            "capacidad": self.capacidad,
        }

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "PlanDespacho":
        try:
            return cls(
                texto_obligatorio(datos["transporte"], "Transporte"),
                texto_obligatorio(datos["nombre"], "Nombre del transporte"),
                exigir_entero(datos["unidades"], "Unidades", minimo=1),
                exigir_entero(datos["capacidad"], "Capacidad", minimo=1),
            )
        except (KeyError, TypeError) as error:
            raise ReglaNegocioError("Despacho guardado incompleto") from error


class Transporte(ABC):
    """Contrato de despacho. La bodega no pregunta qué camión concreto lo atiende."""

    @property
    @abstractmethod
    def clave(self) -> str:
        """Clave estable para guardar el despacho."""

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre visible del vehículo."""

    @property
    @abstractmethod
    def capacidad(self) -> int:
        """Máximo de prendas que caben en un viaje."""

    @property
    def carga_minima(self) -> int:
        """Mínimo de prendas para que el viaje se justifique. Por defecto, una."""
        return 1

    def descripcion(self) -> str:
        return f"{self.nombre}: de {self.carga_minima} a {self.capacidad} prendas"

    def motivo_rechazo(self, unidades: int) -> str | None:
        """None si puede llevar la carga; si no, explica por qué."""
        if unidades > self.capacidad:
            return f"supera su capacidad de {self.capacidad} prendas"
        if unidades < self.carga_minima:
            return f"requiere al menos {self.carga_minima} prendas"
        return None

    def puede_transportar(self, unidades: int) -> bool:
        return self.motivo_rechazo(unidades) is None

    def planificar(self, unidades: int) -> PlanDespacho:
        """Plantilla común: valida con las reglas de cada vehículo y arma el plan del viaje."""
        unidades = exigir_entero(unidades, "Unidades a despachar", minimo=1)
        motivo = self.motivo_rechazo(unidades)
        if motivo:
            raise ReglaNegocioError(f"{self.nombre} no sirve para {unidades} prendas: {motivo}")
        return PlanDespacho(self.clave, self.nombre, unidades, self.capacidad)


class CamionLiviano(Transporte):
    """Camión 3/4: reparto urbano, entra a cualquier calle. Sirve para reposiciones chicas."""

    @property
    def clave(self) -> str:
        return "liviano"

    @property
    def nombre(self) -> str:
        return "Camión 3/4 (liviano)"

    @property
    def capacidad(self) -> int:
        return 300


class CamionPesado(Transporte):
    """Camión pesado: grandes reabastecimientos. Tiene carga mínima porque no conviene
    sacarlo casi vacío y dejar la bodega sin él."""

    @property
    def clave(self) -> str:
        return "pesado"

    @property
    def nombre(self) -> str:
        return "Camión pesado"

    @property
    def capacidad(self) -> int:
        return 3000

    @property
    def carga_minima(self) -> int:
        return 200


TRANSPORTES: tuple[type[Transporte], ...] = (CamionLiviano, CamionPesado)


def transporte_por_nombre(nombre: str) -> Transporte:
    for clase in TRANSPORTES:
        transporte = clase()
        if nombre.strip() in (transporte.nombre, transporte.clave):
            return transporte
    raise ReglaNegocioError("Selecciona un transporte para el despacho")
