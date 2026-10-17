# Imagem oficial recomendada pelo osmnx
FROM continuumio/miniconda3:latest

WORKDIR /app

# Instala tudo
RUN conda install -y --no-update-deps -c conda-forge \
    python=3.10 \
    osmnx \
    dash \
    dash-leaflet \
    pandas \
    numpy \
    && conda clean -a -y

COPY . /app/

# porta dash padrao 8050
EXPOSE 8050

# Comandos para iniciar
CMD ["python", "app.py"]