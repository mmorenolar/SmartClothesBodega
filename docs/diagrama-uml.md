# Diagrama de clases

```mermaid
classDiagram
    class Producto {
        <<abstract>>
        -sku
        -nombre
        -foto
        -stock
        -talla
        -color
        -estado
        +tipo*
        +detalle*
        +tallas_validas()*
        +actualizar_especifico(extra)*
        +validar_salida(cantidad)
        +descontar(cantidad)
        +reponer(cantidad)
        -__actualizar_estado()
    }
    class Pantalon {
        -corte
    }
    class Calzado {
        -estilo
    }
    class Polera
    class EstadoProducto {
        <<enumeration>>
        DISPONIBLE
        AGOTADO
    }
    Producto <|-- Pantalon
    Producto <|-- Calzado
    Producto <|-- Polera
    Producto --> EstadoProducto

    class SalidaBodega {
        <<abstract>>
        -folio
        -fecha
        +unidades
        +lineas()*
        +marcar_aplicada()*
        +comprobante(catalogo)
    }
    class OrdenTraslado {
        -tienda_codigo
        -estado
        +agregar(producto, cantidad)
        +quitar(sku)
        +anular()
        +cotizar(transporte) PlanDespacho
    }
    class RegistroMerma {
        -sku
        -cantidad
        -motivo
        -observacion
    }
    class DetalleTraslado {
        -sku
        -nombre
        -foto
        -talla
        -color
        -cantidad
    }
    class EstadoOrden {
        <<enumeration>>
        BORRADOR
        CONFIRMADA
        ANULADA
    }
    class MotivoMerma {
        <<enumeration>>
        DANO
        PERDIDA
        FALLA_FABRICA
    }
    SalidaBodega <|-- OrdenTraslado
    SalidaBodega <|-- RegistroMerma
    OrdenTraslado *-- DetalleTraslado
    OrdenTraslado --> EstadoOrden
    OrdenTraslado --> Tienda
    RegistroMerma --> MotivoMerma
    DetalleTraslado ..> Producto : copia datos

    class Transporte {
        <<abstract>>
        +nombre*
        +capacidad*
        +carga_minima
        +costo(unidades)*
        +motivo_rechazo(unidades)
        +planificar(unidades) PlanDespacho
    }
    class CamionLiviano {
        capacidad = 300
        costo = 35.000 + 120 x prenda
    }
    class CamionPesado {
        capacidad = 3000
        carga_minima = 200
        costo = 120.000 + 40 x prenda
    }
    class PlanDespacho {
        transporte
        unidades
        capacidad
        costo
        ocupacion
    }
    Transporte <|-- CamionLiviano
    Transporte <|-- CamionPesado
    Transporte ..> PlanDespacho : crea
    OrdenTraslado --> PlanDespacho : despacho

    class Tienda {
        -codigo
        -nombre
        -direccion
    }

    class SmartClothes {
        +registrar_producto()
        +ingresar_stock(sku, cantidad)
        +crear_orden(tienda, fecha)
        +agregar_a_orden(folio, sku, cantidad)
        +cotizar_despachos(folio)
        +transporte_sugerido(folio)
        +confirmar_orden(folio, transporte)
        +registrar_merma(sku, cantidad, motivo, obs)
        +emitir_comprobante(folio)
        -_aplicar_salida(salida)
    }
    class RepositorioJSON
    class Controlador
    class Aplicacion
    SmartClothes o-- Producto
    SmartClothes o-- Tienda
    SmartClothes o-- OrdenTraslado
    SmartClothes o-- RegistroMerma
    SmartClothes --> RepositorioJSON
    Controlador --> SmartClothes
    Aplicacion --> Controlador
```

`SmartClothes.confirmar_orden` recibe cualquier `Transporte` y la orden llama a `planificar()`. Cada camión responde con su propia capacidad, carga mínima y tarifa. Agregar un furgón, por ejemplo, es crear `class Furgon(Transporte)` y sumarlo a `TRANSPORTES`, sin modificar `OrdenTraslado` ni `SmartClothes`.

`SmartClothes._aplicar_salida` recibe cualquier `SalidaBodega`: recorre `lineas()`, valida y descuenta con `Producto.descontar()`, y luego llama a `marcar_aplicada()`. No tiene una rama para traslados y otra para mermas. Para sumar un nuevo tipo de salida (por ejemplo, una devolución a proveedor) basta con crear otra subclase.
