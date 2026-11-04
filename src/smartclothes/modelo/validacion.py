"""Validaciones compartidas por el modelo. No dependen de la interfaz."""

from datetime import date, datetime

from smartclothes.modelo.errores import ReglaNegocioError

FORMATO_FECHA = "%d-%m-%Y"


def texto_obligatorio(valor: object, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ReglaNegocioError(f"{campo} es obligatorio")
    return valor.strip()


def exigir_entero(valor: object, campo: str, minimo: int) -> int:
    if type(valor) is not int:
        raise ReglaNegocioError(f"{campo} debe ser un número entero")
    if valor < minimo:
        if minimo == 1:
            raise ReglaNegocioError(f"{campo} debe ser un entero mayor que cero")
        if minimo == 0:
            raise ReglaNegocioError(f"{campo} debe ser un entero mayor o igual a cero")
        raise ReglaNegocioError(f"{campo} debe ser un entero mayor o igual a {minimo}")
    return valor


def opcion(valor: object, opciones: tuple[str, ...], campo: str) -> str:
    """Acepta una de las opciones sin importar mayúsculas y devuelve la forma oficial."""
    limpio = texto_obligatorio(valor, campo)
    for permitida in opciones:
        if permitida.lower() == limpio.lower():
            return permitida
    raise ReglaNegocioError(f"{campo} debe ser una de estas opciones: {', '.join(opciones)}")


def sku_valido(valor: object) -> str:
    """SKU en mayúsculas: letras, números y guiones. Ej.: POL-BAS-BL-M."""
    sku = texto_obligatorio(valor, "SKU").upper()
    if len(sku) < 3:
        raise ReglaNegocioError("El SKU debe tener al menos 3 caracteres")
    if not all(caracter.isalnum() or caracter == "-" for caracter in sku):
        raise ReglaNegocioError("El SKU solo admite letras, números y guiones")
    return sku


def exigir_fecha(valor: object, campo: str) -> date:
    if type(valor) is not date:
        raise ReglaNegocioError(f"{campo} debe ser una fecha")
    return valor


def fecha_desde_texto(texto: object, campo: str) -> date:
    limpio = texto_obligatorio(texto, campo)
    try:
        return datetime.strptime(limpio, FORMATO_FECHA).date()
    except ValueError as error:
        raise ReglaNegocioError(f"{campo} debe tener el formato dd-mm-aaaa") from error


def fecha_a_texto(fecha: date) -> str:
    return fecha.strftime(FORMATO_FECHA)
