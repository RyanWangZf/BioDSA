FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends chromium && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pandas==2.3.3 numpy==2.3.4 scipy==1.16.3 matplotlib==3.10.7 seaborn==0.13.2 statsmodels==0.14.5 lifelines==0.30.0 scikit-learn==1.7.2 plotly==6.3.1 kaleido==1.1.0 ridgeplot==0.3.2 PyComplexHeatmap==1.8.3
COPY test.sh grade.py run_submission.py /tests/
COPY references/ /tests/references/
COPY data/ /app/data/
RUN chmod 700 /tests/references && chmod +x /tests/test.sh
WORKDIR /app
