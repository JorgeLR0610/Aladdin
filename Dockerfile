#Usa una imagen oficial de python como base
FROM python:3.11-slim

#Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

#Instala ffmpeg usando apt
RUN apt-get update && apt-get install -y ffmpeg

#Copia el archivo de requisitos e instala las dependencias de python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#Copia el resto del código del bot al contenedor
COPY . .

CMD ["python", "app.py"]
