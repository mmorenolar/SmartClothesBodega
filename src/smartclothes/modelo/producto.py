"""Prendas de la bodega. Pantalón, Calzado y Polera especializan un producto abstracto.

El stock y el estado son privados. Solo cambian con descontar() y reponer(),
y el estado se recalcula solo: con stock 0 queda Agotado.
"""

from abc import ABC, abstractmethod
from enum import Enum

from smartclothes.modelo.errores import ReglaNegocioError
from smartclothes.modelo.validacion import exigir_entero, opcion, sku_valido, texto_obligatorio


class EstadoProducto(Enum):
    DISPONIBLE = "DISPONIBLE"
    AGOTADO = "AGOTADO"

    @property
    def etiqueta(self) -> str:
        return {EstadoProducto.DISPONIBLE: "Disponible", EstadoProducto.AGOTADO: "Agotado"}[self]


class Producto(ABC):
    """Atributos comunes: SKU, nombre, foto, stock, talla, color y estado."""

    def __init__(self, sku: str, nombre: str, foto: str, stock: int, talla: str, color: str):
        self._sku = sku_valido(sku)
        self._nombre = texto_obligatorio(nombre, "Nombre")
        self._foto = texto_obligatorio(foto, "Foto")
        self._talla = opcion(talla, self.tallas_validas(), "Talla")
        self._color = texto_obligatorio(color, "Color")
        self._stock = exigir_entero(stock, "Stock", minimo=0)
        self._estado = EstadoProducto.DISPONIBLE
        self.__actualizar_estado()

    # ----- Lectura pública (sin setters) -----

    @property
    def sku(self) -> str:
        return self._sku

    @property
    def id(self) -> str:
        """Alias del SKU para las colecciones del sistema."""
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
    def stock(self) -> int:
        return self._stock

    @property
    def estado(self) -> EstadoProducto:
        return self._estado

    @property
    def disponible(self) -> bool:
        return self._estado is EstadoProducto.DISPONIBLE

    # ----- Contrato que cada prenda implementa (polimorfismo) -----

    @property
    @abstractmethod
    def tipo(self) -> str:
        """Clave estable para guardar el producto."""

    @property
    @abstractmethod
    def tipo_visible(self) -> str:
        """Nombre del tipo para mostrar en pantalla."""

    @property
    @abstractmethod
    def detalle(self) -> str:
        """Dato propio de la prenda: corte, estilo o nada."""

    @classmethod
    @abstractmethod
    def tallas_validas(cls) -> tuple[str, ...]:
        """Cada tipo de prenda usa su propia tabla de tallas."""

    @abstractmethod
    def actualizar_especifico(self, extra: object) -> None:
        """Actualiza el corte o el estilo. La polera no tiene dato extra."""

    @abstractmethod
    def _extras(self) -> dict:
        """Campos propios de la subclase para guardar en JSON."""

    # ----- Operaciones encapsuladas -----

    def descripcion(self) -> str:
        nombre = self._nombre
        if not nombre.lower().startswith(self.tipo_visible.lower()):
            nombre = f"{self.tipo_visible} {nombre}"
        texto = f"{nombre} · Talla {self._talla} · {self._color}"
        return f"{texto} · {self.detalle}" if self.detalle else texto

    def actualizar(self, nombre: str, foto: str, talla: str, color: str) -> None:
        """Edita los datos descriptivos. El stock y el estado no se tocan aquí."""
        nombre_limpio = texto_obligatorio(nombre, "Nombre")
        foto_limpia = texto_obligatorio(foto, "Foto")
        talla_limpia = opcion(talla, self.tallas_validas(), "Talla")
        color_limpio = texto_obligatorio(color, "Color")
        self._nombre = nombre_limpio
        self._foto = foto_limpia
        self._talla = talla_limpia
        self._color = color_limpio

    def validar_salida(self, cantidad: int) -> int:
        """Comprueba estado Disponible y stock suficiente sin modificar nada."""
        cantidad_valida = exigir_entero(cantidad, "Cantidad", minimo=1)
        if not self.disponible:
            raise ReglaNegocioError(f"{self._sku} está {self._estado.etiqueta.lower()} y no puede salir de bodega")
        if cantidad_valida > self._stock:
            raise ReglaNegocioError(f"Stock insuficiente de {self._sku}. Disponible en bodega: {self._stock}")
        return cantidad_valida

    def descontar(self, cantidad: int) -> None:
        cantidad_valida = self.validar_salida(cantidad)
        self._stock -= cantidad_valida
        self.__actualizar_estado()

    def reponer(self, cantidad: int) -> None:
        self._stock += exigir_entero(cantidad, "Cantidad", minimo=1)
        self.__actualizar_estado()

    def __actualizar_estado(self) -> None:
        """Privado: nadie fuera de la clase puede fijar el estado a mano."""
        self._estado = EstadoProducto.AGOTADO if self._stock == 0 else EstadoProducto.DISPONIBLE

    # ----- JSON -----

    def a_diccionario(self) -> dict:
        datos = {
            "sku": self._sku,
            "tipo": self.tipo,
            "nombre": self._nombre,
            "foto": self._foto,
            "stock": self._stock,
            "talla": self._talla,
            "color": self._color,
            "estado": self._estado.value,
        }
        datos.update(self._extras())
        return datos

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._sku!r}, stock={self._stock}, {self._estado.etiqueta})"


class Pantalon(Producto):
    CORTES = ("Slim", "Regular", "Skinny")
    TALLAS = ("36", "38", "40", "42", "44", "46", "48", "50")

    def __init__(self, sku: str, nombre: str, foto: str, stock: int, talla: str, color: str, corte: str):
        super().__init__(sku, nombre, foto, stock, talla, color)
        self._corte = opcion(corte, self.CORTES, "Corte")

    @property
    def tipo(self) -> str:
        return "pantalon"

    @property
    def tipo_visible(self) -> str:
        return "Pantalón"

    @property
    def corte(self) -> str:
        return self._corte

    @property
    def detalle(self) -> str:
        return f"Corte {self._corte}"

    @classmethod
    def tallas_validas(cls) -> tuple[str, ...]:
        return cls.TALLAS

    def actualizar_especifico(self, extra: object) -> None:
        self._corte = opcion(extra, self.CORTES, "Corte")

    def _extras(self) -> dict:
        return {"corte": self._corte}


class Calzado(Producto):
    ESTILOS = ("Deportivo", "Casual", "Formal")
    TALLAS = tuple(str(numero) for numero in range(35, 47))

    def __init__(self, sku: str, nombre: str, foto: str, stock: int, talla: str, color: str, estilo: str):
        super().__init__(sku, nombre, foto, stock, talla, color)
        self._estilo = opcion(estilo, self.ESTILOS, "Estilo")

    @property
    def tipo(self) -> str:
        return "calzado"

    @property
    def tipo_visible(self) -> str:
        return "Calzado"

    @property
    def estilo(self) -> str:
        return self._estilo

    @property
    def detalle(self) -> str:
        return f"Estilo {self._estilo}"

    @classmethod
    def tallas_validas(cls) -> tuple[str, ...]:
        return cls.TALLAS

    def actualizar_especifico(self, extra: object) -> None:
        self._estilo = opcion(extra, self.ESTILOS, "Estilo")

    def _extras(self) -> dict:
        return {"estilo": self._estilo}


class Polera(Producto):
    """Usa solo la estructura base. No agrega atributos."""

    TALLAS = ("XS", "S", "M", "L", "XL", "XXL")

    @property
    def tipo(self) -> str:
        return "polera"

    @property
    def tipo_visible(self) -> str:
        return "Polera"

    @property
    def detalle(self) -> str:
        return ""

    @classmethod
    def tallas_validas(cls) -> tuple[str, ...]:
        return cls.TALLAS

    def actualizar_especifico(self, extra: object) -> None:
        return None

    def _extras(self) -> dict:
        return {}


TIPOS_PRODUCTO: dict[str, type[Producto]] = {
    "Pantalón": Pantalon,
    "Calzado": Calzado,
    "Polera": Polera,
}


def crear_producto(tipo: str, sku: str, nombre: str, foto: str, stock: int, talla: str, color: str,
                   extra: object = None) -> Producto:
    clase = TIPOS_PRODUCTO.get(tipo)
    if clase is None:
        raise ReglaNegocioError("El producto debe ser Pantalón, Calzado o Polera")
    if clase is Polera:
        return Polera(sku, nombre, foto, stock, talla, color)
    return clase(sku, nombre, foto, stock, talla, color, extra)


def producto_desde_diccionario(datos: dict) -> Producto:
    if not isinstance(datos, dict):
        raise ReglaNegocioError("El producto guardado no tiene el formato esperado")
    try:
        tipo = datos["tipo"]
        comunes = (
            str(datos["sku"]),
            datos["nombre"],
            datos["foto"],
            datos["stock"],
            str(datos["talla"]),
            datos["color"],
        )
        if tipo == "pantalon":
            producto: Producto = Pantalon(*comunes, datos["corte"])
        elif tipo == "calzado":
            producto = Calzado(*comunes, datos["estilo"])
        elif tipo == "polera":
            producto = Polera(*comunes)
        else:
            raise ReglaNegocioError("Tipo de producto desconocido")
    except KeyError as error:
        raise ReglaNegocioError("Producto guardado incompleto") from error
    if "estado" in datos and datos["estado"] != producto.estado.value:
        raise ReglaNegocioError(f"El estado guardado de {producto.sku} no coincide con su stock")
    return producto
