# Utiliza una imagen base de Python que incluya el sistema operativo y Python
FROM python:3.11-slim
ENV PYTHONUNBUFFERED 1

RUN apt-get update && pip install -U poetry

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo pyproject.toml y el archivo poetry.lock a la imagen
COPY pyproject.toml poetry.lock /app/

RUN cd /app && poetry export -f requirements.txt --output /app/requirements.txt --without-hashes --dev && pip install --no-warn-script-location --disable-pip-version-check --no-cache-dir -r /app/requirements.txt

# Copia el resto de los archivos de la aplicación a la imagen
COPY . /app/

EXPOSE 5000
CMD ["python", "app.py"]
