# Usar una imagen base de Python
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para Chromium y ChromeDriver
RUN apt-get update && \
    apt-get install -y chromium chromium-driver fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

ENV CHROME_BINARY=/usr/bin/chromium

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar las dependencias de Python (comentario para invalidar caché)
RUN pip install --no-cache-dir -r requirements.txt

# Instalar los navegadores para Playwright
RUN playwright install --with-deps

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto que Render usará
EXPOSE 10000

# Comando para iniciar la aplicación
# Render proporciona la variable de entorno $PORT, Gunicorn la usará.
CMD gunicorn --chdir src --bind "0.0.0.0:$PORT" app:app
