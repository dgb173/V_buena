# Usar una imagen base de Python
FROM python:3.11-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar los navegadores para Playwright
RUN playwright install --with-deps

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto que Render usará
EXPOSE 10000

# Comando para iniciar la aplicación
# Render proporciona la variable de entorno $PORT, Gunicorn la usará.
CMD ["gunicorn", "--chdir", "src", "--bind", "0.0.0.0:$PORT", "app:app"]
