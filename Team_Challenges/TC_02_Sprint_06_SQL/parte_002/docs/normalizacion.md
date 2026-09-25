# Justificación de la normalización hasta 3NF

Modelo de datos de **VoltiaTech** · 7 tablas · Google BigQuery

Este documento demuestra que el modelo cumple las tres primeras formas normales y justifica
las decisiones de diseño que el enunciado pedía razonar.

---

## 1NF — Primera Forma Normal

> *Todos los atributos son atómicos y no hay grupos repetidos.*

**Se cumple.** Ningún campo del modelo guarda listas, valores múltiples ni estructuras
anidadas:

- El nombre del cliente está partido en `first_name` y `last_name`, no en un único campo
  "nombre completo" que después habría que trocear para ordenar por apellido.
- La dirección de envío está partida en `shipping_country` y `shipping_city`, porque el
  análisis geográfico necesita el país como valor propio.
- **El caso crítico son los productos de un pedido.** La tentación de novato es guardar en
  `orders` un campo `productos = "12, 45, 7"`. Eso viola la 1NF de forma flagrante: el campo
  no sería atómico, no se podría hacer un `JOIN` con `products`, ni contar unidades, ni
  calcular márgenes sin parsear texto. En su lugar, **cada producto de cada pedido es una
  fila propia en `order_items`**.

BigQuery admite tipos `ARRAY` y `STRUCT` que técnicamente romperían la 1NF, y en un
escenario analítico puro podrían justificarse por rendimiento. Aquí no se usan: el enunciado
pide un modelo relacional normalizado, y la desnormalización sería una optimización
prematura sobre un volumen de datos pequeño.

---

## 2NF — Segunda Forma Normal

> *Cumple 1NF y no hay dependencias parciales: ningún atributo no-clave depende de solo
> una parte de la clave primaria.*

**Se cumple.** La 2NF solo puede violarse en tablas con **clave compuesta**, así que el
punto de riesgo del modelo es `order_items`, que es la tabla de unión.

Un diseño alternativo habría sido darle a `order_items` la clave compuesta
`(order_id, product_id)`. Con esa clave aparecería el problema: al añadir
`product_name` a la tabla, ese campo dependería **solo de `product_id`**, no de la clave
completa. Eso es una dependencia parcial, y violaría la 2NF.

**Cómo lo evita el modelo:**

1. `order_items` usa una **clave primaria simple y artificial**, `order_item_id`. Con una
   clave de un solo atributo, las dependencias parciales son imposibles por definición.
2. Los atributos que sí están en `order_items` —`quantity`, `unit_price`, `discount_pct`—
   dependen de la combinación pedido-producto y **de nada más**: la cantidad de un producto
   concreto en un pedido concreto no tiene sentido fuera de esa intersección.
3. Lo que depende solo del producto (`product_name`, `price`, `cost`, `stock`) vive en
   `products`. Lo que depende solo del pedido (`status`, fechas, destino) vive en `orders`.

La clave artificial tiene además una ventaja práctica: **`reviews` puede referenciar una
línea concreta con una sola FK** (`order_item_id`) en lugar de arrastrar una FK compuesta de
dos columnas.

---

## 3NF — Tercera Forma Normal

> *Cumple 2NF y no hay dependencias transitivas: ningún atributo no-clave depende de otro
> atributo no-clave.*

**Se cumple.** Los dos puntos donde podía aparecer una dependencia transitiva:

**a) Producto y categoría.** Si `products` guardara `category_name` además de `category_id`,
la cadena sería `product_id → category_id → category_name`: una dependencia transitiva. El
nombre de la categoría no depende del producto, depende de la categoría. Por eso existe la
tabla `categories` y `products` solo guarda la FK. Renombrar "Audio" a "Sonido" es entonces
un `UPDATE` de una fila, y no de los 70 productos de esa categoría.

**b) Pedido y cliente.** `orders` guarda `customer_id`, pero **no** `customer_name` ni
`customer_email`. Si los guardara, la cadena sería `order_id → customer_id →
customer_name`, otra transitividad. El nombre del cliente se obtiene con un `JOIN`, que es exactamente para
lo que existen los `JOIN`.

---

## Las tres preguntas del enunciado

### ¿Por qué `unit_price` está en `order_items` y no se lee de `products.price`?

**Porque son dos cosas distintas.** `products.price` es *el precio actual del catálogo*;
`order_items.unit_price` es *el precio que el cliente pagó aquel día*.

Si el análisis leyera el precio desde `products`, cada cambio de tarifa **reescribiría
retroactivamente la facturación histórica**: subir hoy el precio de un portátil haría que el
informe de ingresos del año pasado creciera solo. Un desastre contable, y además imposible
de auditar.

**Esto no viola la 3NF**, aunque a primera vista parezca redundancia. No lo es porque
`unit_price` **no depende de `product_id`**: depende de la combinación producto-pedido, es
decir, del momento de la transacción. Dos líneas del mismo producto en fechas distintas
pueden tener `unit_price` diferente, y eso es correcto. Es un **dato histórico**, no una
copia de otro campo. El mismo razonamiento se aplica a `discount_pct`.

### ¿Por qué `country` está en `customers` y no en una tabla `countries` separada?

Una tabla `countries` estaría justificada si el país tuviera **atributos propios** que
dependieran solo de él: código ISO, moneda, tipo de IVA, zona de envío... En ese caso,
guardar la moneda en `customers` sería una dependencia transitiva
(`customer_id → country → currency`) y habría que separarla.

En este modelo el país es **solo una etiqueta**: no arrastra ningún atributo adicional.
Extraerlo a su propia tabla añadiría un `JOIN` a casi todas las queries analíticas sin
eliminar ninguna redundancia real. Sería normalización por deporte, no por necesidad.

**Cuándo cambiaría la decisión:** en cuanto el negocio necesite IVA por país o costes de
envío por zona. Entonces `countries` se convierte en obligatoria, porque esos atributos sí
dependen del país y no del cliente.

### Si `orders` almacenase `customer_name` además de `customer_id`, ¿qué forma normal se violaría?

Se violaría la **3NF**, por dependencia transitiva.

La cadena sería `order_id → customer_id → customer_name`: el nombre del cliente **no depende
del pedido**, depende del cliente, que es a su vez un atributo no-clave de `orders`. Justo la
definición de dependencia transitiva.

Los problemas concretos que causaría:

- **Anomalía de actualización.** Un cliente que se casa y cambia de apellido obliga a
  actualizar todas sus filas de `orders`. Si una se queda sin actualizar, la base de datos
  se contradice a sí misma y ya no hay forma de saber cuál es el nombre bueno.
- **Anomalía de inserción.** No se podría registrar un pedido sin repetir datos que ya
  existen en otro sitio.
- **Espacio desperdiciado.** El nombre se almacena tantas veces como pedidos tenga ese
  cliente.

**El matiz importante:** esto **no** es lo mismo que el caso de `unit_price`. El nombre del
cliente en el momento del pedido no es un dato de negocio que haya que conservar; el precio
pagado sí. La diferencia entre redundancia (mala) y dato histórico (necesario) está en si el
valor **puede cambiar legítimamente con el tiempo sin invalidar el registro pasado**.

---

## Resumen del modelo

| Tabla | PK | FKs | Cardinalidad de la relación |
|---|---|---|---|
| `categories` | `category_id` | — | — |
| `customers` | `customer_id` | — | — |
| `products` | `product_id` | `category_id` | N productos : 1 categoría |
| `orders` | `order_id` | `customer_id` | N pedidos : 1 cliente |
| `order_items` | `order_item_id` | `order_id`, `product_id` | **Resuelve N pedidos : M productos** |
| `payments` | `payment_id` | `order_id` | N pagos : 1 pedido |
| `reviews` | `review_id` | `order_item_id` | N valoraciones : 1 línea de pedido |

**Por qué `payments` permite varias filas por pedido** (N:1 y no 1:1): un pedido puede
cobrarse y después reembolsarse, o fallar un cobro y reintentarlo. Forzar 1:1 impediría
registrar ese historial.

**Por qué `reviews` cuelga de `order_items` y no de `orders`:** un pedido con tres productos
puede dejar al cliente encantado con dos y decepcionado con el tercero. Colgando la
valoración del pedido completo constaría que algo falló, pero no **qué producto**, y el
análisis de calidad del catálogo sería imposible.
