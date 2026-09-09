# Armar la tienda Shopify (páginas + calculadora)

La descripción del producto **no cambia el color de la tienda**. El fondo blanco se quita en **Themes → Customize → Custom Liquid** (pasos abajo).

Correo/Resend queda **pausado**. El cobro + webhook ya funcionan. Esto es la vitrina.

Archivos en esta carpeta:

| Archivo | Dónde pegarlo |
| --- | --- |
| `home.html` | Inicio → Custom Liquid |
| `calculator.html` | Página **Calculadora** → Custom Liquid |
| `coach.html` | Página **El coach** → Custom Liquid |
| `product-description.html` | Producto → Description |

Tienda: `https://garyfelicien.myshopify.com`  
Producto ID: `10255880847600`

Si el handle del producto no es `plan-personalizado-de-12-semanas`, cambia los `href` y el `CTA_URL` de la calculadora.

---

## 0. Quitar el “Opening soon” (para ver la tienda)

1. Admin → **Online Store → Preferences** (o el candado de la tienda)
2. Desactiva **Password** / “Restrict access to visitors with the password”
3. Save

---

## 1. Producto — nombre y descripción

1. Products → el producto `10255880847600`
2. Title: **Plan personalizado de 12 semanas**
3. Pega `product-description.html` en Description (vista código / HTML si el editor lo permite)
4. Inventory: no trackear stock
5. **This is a physical product**: OFF (digital)
6. Save. Copia la URL pública (`/products/...`).

---

## 2. Página Calculadora

1. **Online Store → Pages → Add page**
2. Title: `Calculadora`
3. Template: default
4. En el cuerpo: deja poco texto (“Tus números de partida”) **o vacío**
5. Save
6. Luego **Online Store → Themes → Customize**
7. Arriba: abre la página **Calculadora** (selector de página)
8. **Add section → Custom Liquid**
9. Pega **todo** `calculator.html`
10. En las primeras líneas del `<script>`, confirma:

```js
var CTA_URL = "https://garyfelicien.myshopify.com/products/TU-HANDLE";
```

11. Save.

---

## 3. Página El coach

Igual que la calculadora: Pages → Add page `El coach` → Customize → Custom Liquid → pega `coach.html`.

---

## 4. Home

1. Themes → **Customize** (página Home)
2. Oculta o borra secciones vacías de Dawn que no sirvan (collage, newsletter si estorban)
3. **Add section → Custom Liquid** (arriba del todo, bajo el header)
4. Pega `home.html`
5. Save

Los `href` `/products/...` y `/pages/calculadora` son rutas de Shopify. Si el handle de la página calculadora es otro, corrígelo en Navigation.

---

## 5. Menú

**Online Store → Navigation → Main menu**

- Inicio → `/`
- Plan → producto
- Calculadora → página calculadora
- El coach → página coach

---

## 6. Tema oscuro (opcional pero recomendable)

Dawn es claro por defecto. En Customize → **Theme settings → Colors**:
- Background: `#0b0c0f`
- Text: `#f3ede2`
- Buttons: `#d4a017`

Si no lo cambias, los bloques Custom Liquid **ya van en negro/dorado** por su propio CSS.

---

## 7. Imágenes

Hoy apuntan a Railway (`…/img/gary-lift.jpg`). Cuando quieras independencia:

1. Shopify → **Content → Files** → sube las fotos de `web/img/`
2. Reemplaza las URLs en `home.html` y `coach.html`

---

## Qué no hacemos todavía

- Resend / correo automático (pausado; el link se puede mandar a mano desde `/admin`)
- Lead magnet H (resumen + 1 día por email)
- Videos YouTube (cuando haya IDs)
