"""Arma la Orden de Traslado y el Registro de Merma como una hoja HTML lista para imprimir.

El navegador se encarga de imprimir o de guardar como PDF. Las fotos van
incrustadas dentro del archivo, así la hoja se ve igual en cualquier computador.
"""

import base64
from html import escape
from pathlib import Path

ESTILO = """
* { box-sizing: border-box; }
body { margin: 0; background: #eef0f3; font-family: "Segoe UI", Inter, Arial, sans-serif; color: #1f2430; }
.hoja { width: 210mm; min-height: 297mm; margin: 24px auto; background: #fff; padding: 18mm 16mm;
        box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.cabecera { display: flex; justify-content: space-between; align-items: flex-start;
            border-bottom: 3px solid #2f6fed; padding-bottom: 14px; }
.marca { display: flex; gap: 12px; align-items: center; }
.logo { width: 46px; height: 46px; background: #2f6fed; color: #fff; font-weight: 700; font-size: 18px;
        display: flex; align-items: center; justify-content: center; border-radius: 6px; }
.marca h1 { margin: 0; font-size: 20px; }
.marca p { margin: 2px 0 0; color: #6b7280; font-size: 12px; }
.folio { border: 2px solid #2f6fed; border-radius: 6px; padding: 8px 16px; text-align: center; min-width: 190px; }
.folio .tipo { font-size: 11px; font-weight: 700; letter-spacing: .08em; color: #2f6fed; text-transform: uppercase; }
.folio .numero { font-size: 22px; font-weight: 700; margin-top: 2px; }
.datos { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 24px; margin: 18px 0; }
.dato { background: #f8f9fb; border-radius: 6px; padding: 10px 12px; }
.dato .etiqueta { font-size: 10px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: .06em; }
.dato .valor { font-size: 14px; margin-top: 3px; }
table { width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 13px; }
th { text-align: left; font-size: 10px; color: #6b7280; text-transform: uppercase; letter-spacing: .06em;
     border-bottom: 2px solid #e3e6eb; padding: 8px 6px; }
td { border-bottom: 1px solid #eef0f3; padding: 8px 6px; vertical-align: middle; }
td.num, th.num { text-align: right; }
td img { width: 52px; height: 52px; object-fit: contain; background: #f8f9fb; border-radius: 4px; display: block; }
.sku { font-family: Consolas, "Courier New", monospace; font-size: 12px; color: #4b5563; }
.total { display: flex; justify-content: flex-end; align-items: center; gap: 18px; margin-top: 12px; }
.total div { background: #2f6fed; color: #fff; border-radius: 6px; padding: 10px 18px; font-size: 14px; }
.total div b { font-size: 18px; margin-left: 10px; }
.observacion { border-left: 4px solid #a85f00; background: #fff3dd; padding: 10px 14px; border-radius: 4px; margin: 14px 0; }
.firmas { display: flex; gap: 40px; margin-top: 70px; }
.firma { flex: 1; border-top: 1px solid #1f2430; padding-top: 6px; text-align: center; font-size: 12px; color: #6b7280; }
.pie { margin-top: 30px; font-size: 10px; color: #9aa1ac; text-align: center; }
.barra { text-align: center; margin: 18px; }
.barra button { background: #2f6fed; color: #fff; border: 0; border-radius: 6px; padding: 10px 22px; font-size: 14px;
                cursor: pointer; }
@media print {
  body { background: #fff; }
  .hoja { margin: 0; box-shadow: none; width: auto; min-height: auto; padding: 0; }
  .barra { display: none; }
  @page { size: A4; margin: 14mm; }
}
"""


def _imagen(ruta: Path | None) -> str:
    if ruta is None or not Path(ruta).exists():
        return ""
    tipo = {".png": "png", ".gif": "gif", ".jpg": "jpeg", ".jpeg": "jpeg", ".webp": "webp"}.get(
        Path(ruta).suffix.lower(), "png"
    )
    datos = base64.b64encode(Path(ruta).read_bytes()).decode("ascii")
    return f'<img src="data:image/{tipo};base64,{datos}" alt="">'


def _dato(etiqueta: str, valor: str) -> str:
    return f'<div class="dato"><div class="etiqueta">{escape(etiqueta)}</div><div class="valor">{escape(valor)}</div></div>'


def _traslado(datos: dict) -> str:
    filas = "".join(
        f"<tr><td>{_imagen(linea['foto'])}</td><td class='sku'>{escape(linea['sku'])}</td>"
        f"<td>{escape(linea['nombre'])}</td><td>{escape(linea['talla'])}</td><td>{escape(linea['color'])}</td>"
        f"<td class='num'><b>{linea['cantidad']}</b></td></tr>"
        for linea in datos["lineas"]
    )
    return (
        '<div class="datos">'
        + _dato("Tienda destino", datos["tienda"])
        + _dato("Dirección de entrega", datos["direccion"])
        + _dato("Fecha de despacho", datos["fecha"])
        + _dato("Transporte", f"{datos['transporte']} · ocupado al {datos['ocupacion']}%")
        + "</div>"
        "<table><thead><tr><th>Foto</th><th>SKU</th><th>Prenda</th><th>Talla</th><th>Color</th>"
        f"<th class='num'>Cantidad</th></tr></thead><tbody>{filas}</tbody></table>"
        '<div class="total">'
        f'<div>Total de unidades enviadas <b>{datos["unidades"]}</b></div></div>'
        '<div class="firmas"><div class="firma">Despachado por (bodega)</div>'
        '<div class="firma">Transportista</div><div class="firma">Recibido por (tienda)</div></div>'
    )


def _merma(datos: dict) -> str:
    return (
        '<div class="datos">'
        + _dato("Fecha de registro", datos["fecha"])
        + _dato("Motivo", datos["motivo"])
        + "</div>"
        "<table><thead><tr><th>Foto</th><th>SKU</th><th>Prenda</th><th>Talla</th><th>Color</th>"
        "<th class='num'>Cantidad dada de baja</th></tr></thead><tbody>"
        f"<tr><td>{_imagen(datos['foto'])}</td><td class='sku'>{escape(datos['sku'])}</td>"
        f"<td>{escape(datos['nombre'])}</td><td>{escape(datos['talla'])}</td><td>{escape(datos['color'])}</td>"
        f"<td class='num'><b>{datos['unidades']}</b></td></tr></tbody></table>"
        f'<div class="observacion"><b>Observación:</b> {escape(datos["observacion"])}</div>'
        '<div class="firmas"><div class="firma">Responsable de bodega</div>'
        '<div class="firma">Supervisor</div></div>'
    )


def documento_html(datos: dict, imprimir: bool = False) -> str:
    """Devuelve la página completa. Con imprimir=True abre el cuadro de impresión al cargar."""
    cuerpo = _traslado(datos) if datos["tipo"] == "traslado" else _merma(datos)
    script = "<script>window.addEventListener('load', () => setTimeout(() => window.print(), 300));</script>"
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>{escape(datos['titulo'])} {escape(datos['folio'])}</title>
<style>{ESTILO}</style></head>
<body>
<div class="barra"><button onclick="window.print()">Imprimir o guardar como PDF</button></div>
<div class="hoja">
  <div class="cabecera">
    <div class="marca"><div class="logo">SC</div>
      <div><h1>Smart Clothes</h1><p>Bodega principal · Control de inventario y traslados</p></div></div>
    <div class="folio"><div class="tipo">{escape(datos['titulo'])}</div><div class="numero">{escape(datos['folio'])}</div></div>
  </div>
  {cuerpo}
  <div class="pie">Documento emitido por el sistema Smart Clothes · {escape(datos['folio'])}</div>
</div>
{script if imprimir else ""}
</body></html>
"""
