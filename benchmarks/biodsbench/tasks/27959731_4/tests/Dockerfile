FROM python:3.12-slim
RUN pip install --no-cache-dir pandas==2.3.3 seaborn==0.13.2 matplotlib==3.10.7
ENV MPLBACKEND=Agg
COPY test.sh /tests/test.sh
COPY grader.py /tests/grader.py
COPY inputs/ /app/inputs/
RUN chmod +x /tests/test.sh
WORKDIR /app
