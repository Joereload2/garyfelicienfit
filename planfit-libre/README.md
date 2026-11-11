# PlanFit (versión libre)

Formulario que pide los datos de la persona y genera al instante un **plan personalizado
de 12 semanas en PDF** (diseño Gary Felicien Fit, negro y dorado, ~24 páginas): pacto,
glosario, gasto energético, macros, 4 menús, recetario, lista de compra, rutina por días,
sustituciones, hábitos, medidas y planner imprimible de 12 semanas.
Sin pagos, sin claves, sin correo.

## Cómo usarlo

1. Instala Python 3.10 o superior (https://www.python.org/downloads/).
2. Abre una terminal en esta carpeta e instala las dependencias:

   ```
   pip install -r requirements.txt
   ```

3. Arranca el programa:

   ```
   python src/server.py
   ```

4. Abre en el navegador: http://localhost:3000
5. Completa el formulario y pulsa **Generar mi plan**: el PDF se descarga solo.

Para cambiar el puerto: `PORT=8080 python src/server.py` (en Windows: `set PORT=8080` y luego el comando).

## Estructura

- `src/server.py` — servidor web mínimo (formulario + endpoint `POST /api/plan`).
- `src/validate.py` — valida los datos del formulario.
- `src/plan.py` — fórmulas base (calorías, macros, hábitos).
- `src/contenido.py` — menús, recetas, lista de compra, energía y rutina personalizados.
- `src/pdf_builder.py` — arma el PDF (diseño negro y dorado).
- `public/` — formulario (HTML, JS, CSS).
- `assets/` — imágenes del PDF y la fuente (Liberation Sans, licencia libre; si el equipo tiene Arial, usa Arial).

El plan es una orientación general y no sustituye la evaluación de un profesional de la salud.
