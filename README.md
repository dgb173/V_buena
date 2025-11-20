# Match Viewer (Streamlit)

Este repo incluye una app Streamlit lista para mostrar partidos usando `data.json` y, opcionalmente, hacer scraping ligero o un analisis en vivo por ID (requiere navegador).

## Estructura clave
- `streamlit_app.py`: entrada Streamlit, lee `data.json` (o el que subas en la UI) y muestra proximos/finalizados con filtros.
- Boton "Scrapear listas (ligero)": intenta refrescar las listas via requests (y Playwright si estuviera disponible). En Render puede fallar si no hay navegador.
- "Analisis en vivo" por ID: usa `modules.estudio_scraper` (Selenium/Playwright). Requiere navegador/driver disponible; en Render normalmente no funcionara.
- `data.json`: datos scrapeados (se busca en la raiz o en `src/data.json`); tambien puedes subir uno manualmente.
- `src/static/cached_previews/*.json`: si los incluyes, el panel de estudio muestra el analisis cacheado por ID; tambien puedes subir un preview JSON manualmente desde la UI.
- `requirements.txt`: incluye Streamlit.
- `render.yaml`: manifiesto listo para crear el servicio en Render.
- `src/`, `scripts/`: logica original de Flask y scraping; no se usan directamente en la app Streamlit pero se mantienen.

## Ejecutar en local (Streamlit)
```bash
py -m pip install -r requirements.txt
streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port 8501
```
Luego abre `http://localhost:8501`.

## Deploy en Render (Streamlit)
- Tipo de servicio: Web Service.
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run streamlit_app.py --server.address 0.0.0.0 --server.port $PORT`
- Entorno recomendado: Python 3.10.13.
- Si no subes `data.json` en el repo, usa el uploader de la barra lateral para cargarlo en runtime.
- Alternativa: usa `render.yaml` para crear el servicio directamente desde Render (autollenara comandos y variables).
- Panel de estudio: sube o incluye `cached_previews/<id>.json` y selecciona/ingresa el ID en la app Streamlit.
- Boton "Scrapear listas (ligero)": puede fallar en Render si Playwright/browsers no estan instalados; en ese caso, sube `data.json` ya generado o usa el uploader de previews.
- "Analisis en vivo" por ID solo funciona en entornos con navegador/driver; no es fiable en Render. Para Render, usa JSON cacheados o el uploader de previews.

## Notas
- La app Streamlit no usa Playwright ni Selenium para las vistas basicas; requiere que le des un `data.json` ya listo o uses el scrap ligero.
- Si sigues usando el flujo Flask con scraping, manten `requirements.txt` tal cual y usa `EMPEZAR_AQUI.bat` como antes.
