# Match Viewer (Streamlit)

Este repo ahora incluye una app Streamlit lista para Render que muestra los partidos usando el archivo `data.json` ya generado por tu scraper.

## Estructura clave
- `streamlit_app.py`: entrada Streamlit, lee `data.json` (o el que subas en la UI) y muestra proximos/finalizados con filtros.
- `data.json`: datos scrapeados (se busca en la raiz o en `src/data.json`), o se puede subir uno manualmente.
- `src/`, `scripts/`, etc.: logica original de Flask y scraping; no se usan en la app Streamlit pero se mantienen.
- `requirements.txt`: incluye Streamlit; no hace falta Playwright para esta app.
- `render.yaml`: manifiesto listo para crear el servicio en Render.

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

## Notas
- La app Streamlit no usa Playwright ni Selenium; requiere que le des un `data.json` ya listo.
- Si sigues usando el flujo Flask con scraping, manten `requirements.txt` tal cual y usa `EMPEZAR_AQUI.bat` como antes.
