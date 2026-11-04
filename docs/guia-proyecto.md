# Guía del proyecto Smart Clothes

## Objetivo

Modelar la bodega principal de Smart Clothes con clases, encapsulamiento, abstracción, herencia, polimorfismo y composición. Las reglas viven en el modelo. Tkinter solo presenta datos y envía acciones al controlador. JSON guarda y recupera el estado.

## Recorrido sugerido para la presentación

1. **Negocio.** Mostrar las tres prendas y su atributo especial: corte del pantalón, estilo del calzado y la polera sin extras. Dibujar `BORRADOR → CONFIRMADA` y la salida a `ANULADA`.
2. **Herencia y abstracción.** Abrir `modelo/producto.py`. `Producto` es abstracta; `Pantalon`, `Calzado` y `Polera` implementan `tipo`, `detalle` y `tallas_validas()`.
3. **Encapsulamiento.** Intentar `producto.stock = 5` en la consola: lanza `AttributeError`. El stock solo cambia con `descontar()` o `reponer()`, y el estado lo fija el método privado `__actualizar_estado()`.
4. **Traslado.** Crear una orden, pedir más unidades que el stock (el error sale del modelo, no de la ventana), confirmar y ver el comprobante con folio.
5. **Agotado.** Trasladar todo el stock de una polera: su estado pasa a Agotado y ya no se puede agregar a otra orden. Ingresar unidades la devuelve a Disponible.
6. **Merma.** Registrar una baja con motivo y observación. El stock baja de inmediato y se emite el Registro de Merma.
7. **Polimorfismo.** Mostrar `SmartClothes._aplicar_salida` y `emitir_comprobante`: tratan igual a `OrdenTraslado` y `RegistroMerma` porque ambas cumplen el contrato `SalidaBodega`.
8. **MVC y JSON.** Seguir un clic desde la vista hasta `Controlador`, `SmartClothes` y `RepositorioJSON`. Cerrar y volver a abrir: el stock no se descuenta otra vez y los folios siguen la numeración.

## Qué mirar en la evaluación

| Criterio | Dónde comprobarlo |
| --- | --- |
| Cuatro pilares | `Producto` y `SalidaBodega` con sus subclases; `SmartClothes._aplicar_salida` |
| Reglas de negocio | `tests/test_smartclothes.py` |
| Tkinter y ttk | `src/smartclothes/vista/`, menú Módulos y `Treeview` con fotos |
| MVC | modelo sin Tkinter; vistas sin descontar stock (lo verifica una prueba) |
| JSON | carpeta `data/` y la prueba de recarga |
| Validaciones | `modelo/validacion.py`, controlador y errores del modelo |

## Preguntas que pueden hacer

- ¿Por qué el stock y el estado no tienen setter? Porque el caso exige que solo cambien mediante métodos encapsulados del backend.
- ¿Qué archivo hay que tocar para agregar un tipo de prenda (por ejemplo, Chaqueta)? Solo `producto.py`: una subclase nueva y su entrada en `TIPOS_PRODUCTO`.
- ¿Por qué el comprobante no cambia si después edito la prenda? `DetalleTraslado` copia los datos al momento de agregar la línea.
- ¿Cuándo se descuenta el stock de un traslado? Al confirmar, no al agregar. Mientras está en borrador queda reservado para que dos órdenes no prometan las mismas unidades.
