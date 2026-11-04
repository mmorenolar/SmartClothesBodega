"""Tienda de venta al público que recibe los traslados."""

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.modelo.validacion import texto_obligatorio


class Tienda:
    def __init__(self, codigo: str, nombre: str, direccion: str):
        self._codigo = texto_obligatorio(codigo, "Código").upper()
        self._nombre = texto_obligatorio(nombre, "Nombre")
        self._direccion = texto_obligatorio(direccion, "Dirección")

    @property
    def codigo(self) -> str:
        return self._codigo

    @property
    def id(self) -> str:
        return self._codigo

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def direccion(self) -> str:
        return self._direccion

    @property
    def identificacion(self) -> str:
        return f"{self._codigo} — {self._nombre}"

    def actualizar(self, nombre: str, direccion: str) -> None:
        nombre_limpio = texto_obligatorio(nombre, "Nombre")
        direccion_limpia = texto_obligatorio(direccion, "Dirección")
        self._nombre = nombre_limpio
        self._direccion = direccion_limpia

    def a_diccionario(self) -> dict:
        return {"codigo": self._codigo, "nombre": self._nombre, "direccion": self._direccion}

    @classmethod
    def desde_diccionario(cls, datos: dict) -> "Tienda":
        try:
            return cls(str(datos["codigo"]), datos["nombre"], datos["direccion"])
        except (KeyError, TypeError) as error:
            raise ReglaNegocioError("Tienda guardada incompleta") from error

    def __repr__(self) -> str:
        return f"Tienda({self._codigo!r}, {self._nombre!r})"
