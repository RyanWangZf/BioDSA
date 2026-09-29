FROM python:3.12-slim
RUN pip install --no-cache-dir pandas==2.3.3 numpy==2.3.4 scipy==1.16.3 matplotlib==3.10.7 seaborn==0.13.2 statsmodels==0.14.5 lifelines==0.30.0
COPY data/ /app/data/
WORKDIR /app
