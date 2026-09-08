# Acceso y pruebas — PlanFit

Documento para **pruebas**. No es un login de cliente: el usuario entra con el enlace de un solo uso.

## Datos de ingreso (panel interno)

| Campo | Valor |
| --- | --- |
| App | http://localhost:3000 |
| Admin | http://localhost:3000/admin |
| ADMIN_SECRET | `Z5ybdNf7xluObI6vOEkETT1vAA3isnLU-Xae8qX9W1-HyZInspyc-KJm4OsJKmz_` |

Arranque:

```
cd C:\Users\jose\consul\Documentos\planfit
python src/server.py
```

## Payment ref solo de pruebas (manual)

Usa **siempre** este par en el admin cuando pruebes a mano:

| Campo | Valor |
| --- | --- |
| Email | `prueba@planfit.local` |
| payment_ref | `pay_prueba_manual` |

Tras un pago real en **Shopify**, en el panel (respaldo) usas el **email del pedido** y
`payment_ref` = `shopify_` + el id numérico del pedido (Shopify Admin → Pedidos).

Tras un pago legado de Mercado Pago (Netlify), usas el **email del comprador** y
`payment_ref` = `mp_` + el id del pago (Mercado Pago → Actividad).

`pay_prueba_manual` está reservado para el panel. **Un payment_ref = un plan.** Si ya aparece como *usado*, el siguiente de la serie es:

- `pay_prueba_manual_2`
- `pay_prueba_manual_3`
- …

No reutilices `pay_test_001`, `pay_test_001.` ni `pay_785ccca4` (ya gastados).

Formulario de prueba válido (después de abrir el enlace):

| Campo | Valor |
| --- | --- |
| Nombre | Ana Prueba |
| Edad | 32 |
| Peso | 70 |
| Altura | 165 |
| Sexo | Mujer |
| Objetivo | Bajar de peso |
| Meta | 66 |
| Días | 3 |
| Lugar | Gimnasio |
| Duración | 45 |
| Experiencia | Principiante |
| Foco | Equilibrado |
| Vegetales | Brócoli, Zanahoria, Tomate |
| Frutas | Manzana, Pera, Kiwi |
| Proteína | Pollo |
| Carbo | Arroz |

El plan **no** se ve en la web. El PDF queda en `data/pdfs/` y el correo en `data/outbox/` (SMTP vacío).

## Pruebas automáticas

Sin Node. Solo Python de la librería estándar + reportlab.

```
cd C:\Users\jose\consul\Documentos\planfit
python -m unittest discover -s tests -v
```

Las automáticas **no tocan** `data/store.json` de producción: usan una carpeta temporal.

### Unitarias (`tests/test_validate.py`, `test_plan.py`, `test_store.py`)

- Validación: edad, IMC, meta agresiva, email bloqueado, mínimos de comida.
- Motor: calorías/macros, menús, hábitos (agua/pasos).
- Store: emitir acceso, `payment_ref` duplicado, gastar token solo en POST válido.

### Flujo completo (`tests/test_flujo.py`)

Levanta un servidor de prueba y comprueba:

1. Portada sin calculadora ni PDF.
2. Emitir acceso con el `payment_ref` de pruebas.
3. El mismo `payment_ref` da 409.
4. Abrir el enlace no gasta el token.
5. POST inválido (edad 17) da 400 y el token sigue pendiente.
6. POST válido da 200 **sin** calorías, menús ni PDF en el JSON.
7. Segundo POST da 409.
8. Existe un PDF en el data dir de prueba.
9. Reenviar PDF no cambia el archivo (mismo hash).
