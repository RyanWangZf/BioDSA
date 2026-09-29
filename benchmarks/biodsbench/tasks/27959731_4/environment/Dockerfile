FROM python:3.12-slim
RUN pip install --no-cache-dir pandas==2.3.3 seaborn==0.13.2 matplotlib==3.10.7
ENV MPLBACKEND=Agg
WORKDIR /app
COPY inputs/ /app/inputs/
