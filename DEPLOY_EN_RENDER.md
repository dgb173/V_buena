# Guía de Despliegue Manual en Render (Plan Gratuito)

Esta guía explica cómo desplegar tu aplicación Python en Render utilizando el plan gratuito, sin necesidad de un archivo `render.yaml` y sin vincular una tarjeta de crédito.

## 1. Estructura del Proyecto

Render detectará tu proyecto como una aplicación Python si encuentra un archivo `requirements.txt` en el directorio raíz. La estructura que hemos preparado es la siguiente:

```
/
├── src/
│   └── app.py         # Tu aplicación Flask
├── .python-version    # Especifica la versión de Python (3.11)
├── requirements.txt   # Lista de dependencias de Python
└── ...                # Otros archivos y carpetas
```

## 2. Archivos de Configuración

Asegúrate de que los siguientes archivos estén en tu repositorio:

*   **`requirements.txt`**: Contiene las librerías necesarias. Nos hemos asegurado de que incluya `flask`, `gunicorn`, `pandas`, `playwright`, `beautifulsoup4`, `requests` y `lxml`.
*   **`.python-version`**: Contiene una sola línea: `3.11`. Esto le indica a Render qué versión de Python usar.

## 3. Guía de Configuración Manual en el Panel de Render

Sigue estos pasos para crear tu servicio web:

1.  **Inicia Sesión en Render**: Ve a [dashboard.render.com](https://dashboard.render.com/).

2.  **Crea un Nuevo "Web Service"**:
    *   Haz clic en el botón **"New +"**.
    *   Selecciona **"Web Service"**.

3.  **Conecta tu Repositorio**:
    *   Elige "Build and deploy from a Git repository".
    *   Conecta tu cuenta de GitHub (o GitLab/Bitbucket) y selecciona el repositorio de tu proyecto.

4.  **Configura el Servicio Web**:
    *   **Name**: Elige un nombre único para tu servicio (ej: `mi-app-nowgoal`).
    *   **Region**: Selecciona una región (ej: `Singapore` u `Oregon, USA`, suelen estar disponibles en el plan gratuito).
    *   **Branch**: Asegúrate de que sea tu rama principal (normalmente `main` o `master`).
    *   **Root Directory**: Déjalo en blanco. Render buscará los archivos desde la raíz del repositorio.
    *   **Runtime**: Render debería detectar **"Python"** automáticamente. Si no, selecciónalo.

5.  **Introduce los Comandos de Build y Start**:
    *   **Build Command**:
        ```bash
        pip install -r requirements.txt
        ```
    *   **Start Command**:
        ```bash
        gunicorn --chdir src app:app
        ```
        *   `--chdir src`: Le dice a Gunicorn que se mueva al directorio `src` antes de arrancar.
        *   `app:app`: Le indica que busque un objeto llamado `app` dentro del archivo `app.py`.

6.  **Selecciona el Tipo de Instancia Gratuita**:
    *   Busca la sección **"Instance Type"**.
    *   **MUY IMPORTANTE**: Asegúrate de que la opción **"Free"** esté seleccionada. Esto garantiza que no se te cobrará nada. Las características del plan gratuito son:
        *   CPU y RAM compartidas.
        *   El servicio se suspende tras 15 minutos de inactividad y se reactiva con la siguiente petición (puede tardar unos segundos en arrancar).

7.  **Variables de Entorno (Opcional)**:
    *   Si tu aplicación necesitara claves de API o configuraciones secretas, las añadirías en la sección **"Environment"**.
    *   Haz clic en **"Add Environment Variable"**.
    *   Por ahora, tu aplicación no parece requerir ninguna, pero si en el futuro la necesitas (por ejemplo, una `API_KEY`), aquí es donde la pondrías.

8.  **Crea el Servicio**:
    *   Haz clic en el botón **"Create Web Service"** en la parte inferior.
    *   Render comenzará el proceso de `build` (instalando las dependencias) y luego el despliegue.

## 4. Verificación

*   **Logs**: En el panel de tu servicio, ve a la pestaña **"Logs"** para ver el progreso del despliegue y detectar posibles errores.
*   **URL**: Una vez que el despliegue sea exitoso (verás un mensaje "Live"), tu aplicación estará disponible en la URL que aparece en la parte superior de tu panel de Render (ej: `https://tu-nombre-de-servicio.onrender.com`).

¡Listo! Con estos pasos, tu aplicación estará desplegada y funcionando en el plan gratuito de Render.
