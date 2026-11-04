# Smart Clothes — Bodega principal y traslados

Aplicación de escritorio para administrar el inventario de la bodega principal de Smart Clothes: prendas (pantalones, calzado y poleras), tiendas destino, órdenes de traslado con comprobante y registro de mermas. El caso aplica abstracción, encapsulamiento, herencia y polimorfismo, con arquitectura MVC y persistencia en JSON.

## Ejecutar

**En Windows, la forma más fácil:** descarga el proyecto (botón verde *Code → Download ZIP*), descomprímelo y haz doble clic en `Abrir Smart Clothes.bat`.

También se puede instalar como paquete:

Requiere Python 3.10 o superior (con Tkinter, que viene incluido en el instalador de python.org). Desde la carpeta del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
smartclothes
```

En Windows: `.venv\Scripts\Activate.ps1`.

También funciona sin instalar: `python -m smartclothes` desde la carpeta `src`, o con `PYTHONPATH=src`.

La ventana abre los datos de `data/`. Cada operación vuelve a guardar productos, tiendas, traslados, mermas y los folios.

```bash
python -m unittest discover -s tests -v
smartclothes-demo
```

`smartclothes-demo` recorre registro de prendas, una orden rechazada por stock, la cotización de los dos camiones, un camión pesado rechazado por carga mínima, la confirmación con comprobante, el cambio a Agotado y una merma, sin abrir ventanas.

## Pantallas

Menú lateral con seis módulos (también con **Ctrl + 1 … 6**):

- **Inicio:** indicadores que suben contando, prendas agotadas o con stock bajo (clic para reponer) y últimos documentos.
- **Productos:** buscador, filtros por tipo o agotados, tabla con fotos y ficha lateral para crear, editar e ingresar unidades.
- **Tiendas:** tabla y ficha para crear o editar.
- **Órdenes de traslado:** tres pasos (prendas → transporte → confirmar). Cada camión se muestra como tarjeta con costo y ocupación, y se sugiere el más conveniente.
- **Mermas y pérdidas:** formulario guiado con ficha de la prenda, motivo en botones y contador de caracteres.
- **Comprobantes:** listado filtrable y vista del documento; al confirmar un traslado, un camión cruza la pantalla.

**Fotos:** en la ficha de la prenda, *Elegir imagen…* acepta JPG, PNG, GIF, WEBP o BMP. La foto se achica y se copia como PNG a `data/fotos`, así viaja con el proyecto. Para JPG se usa la librería Pillow, que `Abrir Smart Clothes.bat` instala sola la primera vez.

Los avisos aparecen en la esquina y se van solos; las acciones que no se pueden deshacer piden confirmación. Los colores y fuentes de toda la app están en `src/smartclothes/vista/tema.py`.

## Estados

```text
Producto:          DISPONIBLE ⇄ AGOTADO      (lo decide el stock, nunca el usuario)

Orden de traslado: BORRADOR → CONFIRMADA
                       └────→ ANULADA
```

Una orden se edita solo en Borrador. Confirmada es final: las prendas ya salieron de bodega.

## Reglas

1. Toda prenda tiene SKU, nombre, foto, stock, talla, color y estado. El pantalón agrega **corte** (Slim, Regular, Skinny), el calzado agrega **estilo** (Deportivo, Casual, Formal) y la polera no agrega nada.
2. Cada tipo de prenda valida su propia tabla de tallas: polera XS–XXL, pantalón 36–50, calzado 35–46.
3. El SKU es único, en mayúsculas, con letras, números y guiones.
4. Una orden de traslado lleva fecha de despacho (no anterior a hoy), tienda destino y prendas elegidas por SKU con su cantidad.
5. No se agrega una cantidad mayor que el stock, contando lo ya reservado en otras órdenes en borrador. La prenda debe estar **Disponible**.
6. Al confirmar se vuelve a validar todo y se descuenta el stock de inmediato. Si una línea falla, no se descuenta ninguna.
7. Si el stock llega a cero, el estado cambia solo a **Agotado**. Un ingreso a bodega lo devuelve a **Disponible**.
8. Al confirmar se elige el **transporte**. El **camión 3/4 (liviano)** lleva hasta 300 prendas: $35.000 de tarifa base más $120 por prenda. El **camión pesado** lleva de 200 a 3.000 prendas: $120.000 de tarifa base más $40 por prenda; no sale con menos de 200 porque no conviene moverlo casi vacío. La pantalla cotiza los dos y sugiere el más barato que sirve. Si el camión elegido no sirve para la carga, la orden no se confirma y no se descuenta nada.
9. La confirmación emite un comprobante con folio único (`OT-000001`), fecha de despacho, tienda destino, cada prenda con SKU, foto, nombre, talla, color y cantidad, y el transporte con su ocupación y costo.
10. Una merma pide SKU, cantidad, motivo (Daño, Pérdida, Falla de fábrica) y una observación de al menos 10 caracteres. Descuenta en el momento, puede agotar la prenda y emite un Registro de Merma con folio propio (`ME-000001`).
11. El stock y el estado **no se editan a mano**: solo cambian con `Producto.descontar()` y `Producto.reponer()`. Editar la ficha no toca el stock.
12. No se elimina una prenda con traslados o mermas, ni una tienda con órdenes.
13. Una operación inválida muestra el error y la aplicación sigue abierta.

## Pilares de POO

| Pilar | Dónde se ve |
| --- | --- |
| Abstracción | `Producto`, `SalidaBodega` y `Transporte` son clases abstractas (`abc`). No se instancian. |
| Encapsulamiento | Stock y estado sin setters. Cambian solo con `descontar()` y `reponer()`; el estado se recalcula en el método privado `__actualizar_estado()`. |
| Herencia | `Pantalon`, `Calzado` y `Polera` especializan `Producto`. `OrdenTraslado` y `RegistroMerma` especializan `SalidaBodega`. `CamionLiviano` y `CamionPesado` especializan `Transporte`. |
| Polimorfismo | `OrdenTraslado.cotizar` llama a `transporte.planificar()` sin saber qué camión recibió: cada uno responde con su capacidad, su carga mínima y su tarifa. `SmartClothes._aplicar_salida` recorre `lineas()` y `emitir_comprobante` llama a `comprobante()` sin saber si recibió un traslado o una merma. `detalle` y `tallas_validas()` cambian según la prenda. |
| Composición | Una `OrdenTraslado` contiene varios `DetalleTraslado`. |

## Estructura

```text
src/smartclothes/modelo/          entidades, reglas y SmartClothes
src/smartclothes/persistencia/    lectura y escritura JSON
src/smartclothes/controladores/   traducción de la interfaz al modelo
src/smartclothes/vista/           ventanas Tkinter y ttk
data/                             datos de ejemplo y fotos de las prendas
tests/                            reglas, persistencia y recorrido de pantallas
```

El modelo no importa Tkinter. Las pantallas no descuentan stock ni deciden estados.

## Documentación

- [Diagrama de clases](docs/diagrama-uml.md)
- [Guía del proyecto](docs/guia-proyecto.md)
